import Foundation

struct ClipboardItem: Identifiable, Codable, Equatable {
    let id: UUID
    let text: String
    let timestamp: Date
    let sourceApp: String?

    init(id: UUID = UUID(), text: String, timestamp: Date = Date(), sourceApp: String? = nil) {
        self.id = id
        self.text = text
        self.timestamp = timestamp
        self.sourceApp = sourceApp
    }
}