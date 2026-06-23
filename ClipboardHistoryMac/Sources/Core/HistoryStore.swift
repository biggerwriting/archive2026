import Foundation

final class HistoryStore: ObservableObject {
    @Published private(set) var items: [ClipboardItem] = []

    private let maxItems: Int
    private let storageURL: URL
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    init(maxItems: Int = 200) {
        self.maxItems = maxItems

        let fm = FileManager.default
        let appSupport = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let dir = appSupport.appendingPathComponent("ClipboardHistoryMac", isDirectory: true)
        if !fm.fileExists(atPath: dir.path) {
            try? fm.createDirectory(at: dir, withIntermediateDirectories: true)
        }
        self.storageURL = dir.appendingPathComponent("history.json")
        load()
    }

    func addText(_ text: String, sourceApp: String?) {
        let cleaned = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleaned.isEmpty else { return }

        if items.first?.text == cleaned {
            return
        }

        items.removeAll { $0.text == cleaned }
        items.insert(ClipboardItem(text: cleaned, sourceApp: sourceApp), at: 0)
        if items.count > maxItems {
            items = Array(items.prefix(maxItems))
        }
        save()
    }

    func clear() {
        items.removeAll()
        save()
    }

    func remove(id: UUID) {
        items.removeAll { $0.id == id }
        save()
    }

    private func load() {
        guard let data = try? Data(contentsOf: storageURL) else { return }
        guard let decoded = try? decoder.decode([ClipboardItem].self, from: data) else { return }
        items = Array(decoded.prefix(maxItems))
    }

    private func save() {
        guard let data = try? encoder.encode(items) else { return }
        try? data.write(to: storageURL, options: [.atomic])
    }
}
