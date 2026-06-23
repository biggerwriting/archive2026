const express = require("express");
const path = require("path");
const fs = require("fs");
const multer = require("multer");
const Database = require("better-sqlite3");

const app = express();
const PORT = process.env.PORT || 3000;
const dataDir = path.join(__dirname, "data");
const uploadDir = path.join(__dirname, "uploads");

if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const db = new Database(path.join(dataDir, "events.db"));

db.exec(`
  CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_value INTEGER NOT NULL,
    exact_date TEXT,
    location TEXT NOT NULL,
    person TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    tags TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
  );
`);

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, uploadDir),
  filename: (_req, file, cb) => {
    const safeName = `${Date.now()}-${Math.random().toString(36).slice(2)}-${file.originalname}`;
    cb(null, safeName);
  },
});

const upload = multer({ storage });

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use("/uploads", express.static(uploadDir));
app.use(express.static(path.join(__dirname, "public")));

function parseSourceInput(rawSources) {
  if (!rawSources) return [];
  try {
    const parsed = JSON.parse(rawSources);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((item) => item && item.type && item.content)
      .map((item) => ({
        type: String(item.type).trim(),
        content: String(item.content).trim(),
      }))
      .filter((item) => item.type && item.content);
  } catch (_err) {
    return [];
  }
}

function mapEventRows(rows) {
  return rows.map((row) => ({
    id: row.id,
    time: row.exact_date || `${row.year_value < 0 ? `公元前${Math.abs(row.year_value)}` : row.year_value}`,
    yearValue: row.year_value,
    exactDate: row.exact_date,
    location: row.location,
    person: row.person,
    title: row.title,
    description: row.description,
    tags: row.tags ? row.tags.split(",").map((t) => t.trim()).filter(Boolean) : [],
    createdAt: row.created_at,
    sources: [],
  }));
}

app.get("/api/events", (req, res) => {
  const { startYear, endYear, location, person, tag } = req.query;

  const where = [];
  const params = {};

  if (startYear !== undefined && startYear !== "") {
    where.push("e.year_value >= @startYear");
    params.startYear = Number(startYear);
  }
  if (endYear !== undefined && endYear !== "") {
    where.push("e.year_value <= @endYear");
    params.endYear = Number(endYear);
  }
  if (location) {
    where.push("e.location LIKE @location");
    params.location = `%${location}%`;
  }
  if (person) {
    where.push("e.person LIKE @person");
    params.person = `%${person}%`;
  }
  if (tag) {
    where.push("e.tags LIKE @tag");
    params.tag = `%${tag}%`;
  }

  const whereSql = where.length ? `WHERE ${where.join(" AND ")}` : "";
  const eventRows = db
    .prepare(
      `SELECT e.* FROM events e
       ${whereSql}
       ORDER BY e.year_value ASC, e.id DESC`
    )
    .all(params);

  const events = mapEventRows(eventRows);
  if (!events.length) {
    return res.json([]);
  }

  const eventIds = events.map((event) => event.id);
  const sourceRows = db
    .prepare(
      `SELECT id, event_id, source_type, content
       FROM sources
       WHERE event_id IN (${eventIds.map(() => "?").join(",")})
       ORDER BY id ASC`
    )
    .all(...eventIds);

  const sourceGroup = new Map();
  for (const source of sourceRows) {
    if (!sourceGroup.has(source.event_id)) {
      sourceGroup.set(source.event_id, []);
    }
    sourceGroup.get(source.event_id).push({
      id: source.id,
      type: source.source_type,
      content: source.content,
    });
  }

  for (const event of events) {
    event.sources = sourceGroup.get(event.id) || [];
  }

  return res.json(events);
});

app.post("/api/events", upload.array("files", 20), (req, res) => {
  const { timeType, exactDate, yearValue, location, person, title, description, tags, sources } = req.body;

  const normalizedTimeType = timeType === "bc" ? "bc" : "ad";
  let parsedYear = Number(yearValue);
  if (Number.isNaN(parsedYear) || !Number.isInteger(parsedYear)) {
    return res.status(400).json({ message: "年份必须是整数。" });
  }
  if (parsedYear <= 0) {
    return res.status(400).json({ message: "年份必须大于 0。" });
  }

  if (normalizedTimeType === "bc") {
    parsedYear = -Math.abs(parsedYear);
  }

  if (!location || !person || !title || !description) {
    return res.status(400).json({ message: "地点、人物、事件标题、事件内容为必填项。" });
  }

  const cleanTags = String(tags || "")
    .split(",")
    .map((tagValue) => tagValue.trim())
    .filter(Boolean)
    .join(",");

  const textSources = parseSourceInput(sources);
  const fileSources = (req.files || []).map((file) => ({
    type: file.mimetype.startsWith("image/")
      ? "image"
      : file.mimetype.startsWith("audio/")
      ? "audio"
      : file.mimetype.startsWith("video/")
      ? "video"
      : "file",
    content: `/uploads/${file.filename}`,
  }));

  const allSources = [...textSources, ...fileSources];

  const insertEvent = db.prepare(
    `INSERT INTO events
      (year_value, exact_date, location, person, title, description, tags)
     VALUES
      (@yearValue, @exactDate, @location, @person, @title, @description, @tags)`
  );
  const insertSource = db.prepare(
    `INSERT INTO sources
      (event_id, source_type, content)
     VALUES
      (@eventId, @sourceType, @content)`
  );

  const save = db.transaction(() => {
    const result = insertEvent.run({
      yearValue: parsedYear,
      exactDate: exactDate || null,
      location: location.trim(),
      person: person.trim(),
      title: title.trim(),
      description: description.trim(),
      tags: cleanTags,
    });

    const eventId = result.lastInsertRowid;
    for (const source of allSources) {
      insertSource.run({
        eventId,
        sourceType: source.type,
        content: source.content,
      });
    }

    return Number(eventId);
  });

  const newEventId = save();
  const newEvent = db.prepare("SELECT * FROM events WHERE id = ?").get(newEventId);
  const sourceRows = db
    .prepare("SELECT id, source_type, content FROM sources WHERE event_id = ? ORDER BY id ASC")
    .all(newEventId);

  return res.status(201).json({
    id: newEvent.id,
    time: newEvent.exact_date || `${newEvent.year_value < 0 ? `公元前${Math.abs(newEvent.year_value)}` : newEvent.year_value}`,
    yearValue: newEvent.year_value,
    exactDate: newEvent.exact_date,
    location: newEvent.location,
    person: newEvent.person,
    title: newEvent.title,
    description: newEvent.description,
    tags: newEvent.tags ? newEvent.tags.split(",").map((t) => t.trim()).filter(Boolean) : [],
    createdAt: newEvent.created_at,
    sources: sourceRows.map((item) => ({
      id: item.id,
      type: item.source_type,
      content: item.content,
    })),
  });
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
