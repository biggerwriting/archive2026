import SwiftUI

struct HistoryPanelView: View {
    @ObservedObject var appController: AppController

    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        return formatter
    }()

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Clipboard History")
                    .font(.headline)
                Spacer()
                Button("Clear") {
                    appController.clearAll()
                }
                .keyboardShortcut(.delete, modifiers: [.command])
            }

            if let error = appController.lastErrorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
            }

            if appController.items.isEmpty {
                Text("还没有复制历史")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .padding(.top, 20)
                    .frame(maxWidth: .infinity, alignment: .center)
            } else {
                List {
                    ForEach(Array(appController.items.enumerated()), id: \.element.id) { index, item in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(item.text)
                                .lineLimit(2)
                                .font(.body)
                            HStack {
                                Text(dateFormatter.string(from: item.timestamp))
                                if let sourceApp = item.sourceApp {
                                    Text("· \(sourceApp)")
                                }
                            }
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        }
                        .padding(6)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(index == appController.selectedIndex ? Color.accentColor.opacity(0.2) : Color.clear)
                        .contentShape(Rectangle())
                        .onTapGesture {
                            appController.selectedIndex = index
                        }
                        .onTapGesture(count: 2) {
                            appController.selectedIndex = index
                            appController.pasteSelectedItem()
                        }
                        .contextMenu {
                            Button("删除") {
                                appController.remove(itemID: item.id)
                            }
                        }
                    }
                }
                .listStyle(.plain)
            }

            Text("快捷键: Option+V 打开历史，方向键选择，回车粘贴，Esc 关闭")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .frame(width: 520, height: 420)
    }
}
