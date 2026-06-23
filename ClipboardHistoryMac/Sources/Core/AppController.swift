import AppKit
import Foundation

final class AppController: ObservableObject {
    @Published var selectedIndex: Int = 0
    @Published private(set) var lastErrorMessage: String?

    let historyStore: HistoryStore
    private let monitor: PasteboardMonitor
    private let hotkeyManager: HotkeyManager
    private let pasteInjector: PasteInjector
    private lazy var panelController = HistoryPanelController(appController: self)

    init(
        historyStore: HistoryStore = HistoryStore(),
        monitor: PasteboardMonitor = PasteboardMonitor(),
        hotkeyManager: HotkeyManager = HotkeyManager(),
        pasteInjector: PasteInjector = PasteInjector()
    ) {
        self.historyStore = historyStore
        self.monitor = monitor
        self.hotkeyManager = hotkeyManager
        self.pasteInjector = pasteInjector
    }

    var items: [ClipboardItem] {
        historyStore.items
    }

    func start() {
        monitor.onTextCopied = { [weak self] text, appName in
            guard let self else { return }
            DispatchQueue.main.async {
                self.historyStore.addText(text, sourceApp: appName)
                self.clampSelection()
            }
        }

        hotkeyManager.onHotkeyPressed = { [weak self] in
            DispatchQueue.main.async { self?.showHistoryPanel() }
        }

        monitor.start()
        hotkeyManager.registerOptionV()
    }

    func showHistoryPanel() {
        clampSelection()
        NSApp.activate(ignoringOtherApps: true)
        panelController.show()
    }

    func hideHistoryPanel() {
        panelController.hide()
    }

    func moveSelectionUp() {
        guard !items.isEmpty else { return }
        selectedIndex = max(0, selectedIndex - 1)
    }

    func moveSelectionDown() {
        guard !items.isEmpty else { return }
        selectedIndex = min(items.count - 1, selectedIndex + 1)
    }

    func pasteSelectedItem() {
        guard items.indices.contains(selectedIndex) else { return }
        do {
            try pasteInjector.paste(text: items[selectedIndex].text)
            hideHistoryPanel()
            lastErrorMessage = nil
        } catch PasteInjectionError.accessibilityPermissionMissing {
            lastErrorMessage = "请在系统设置 -> 隐私与安全性 -> 辅助功能中允许本应用。"
        } catch {
            lastErrorMessage = "自动粘贴失败，请重试。"
        }
    }

    func remove(itemID: UUID) {
        historyStore.remove(id: itemID)
        clampSelection()
    }

    func clearAll() {
        historyStore.clear()
        selectedIndex = 0
    }

    private func clampSelection() {
        guard !items.isEmpty else {
            selectedIndex = 0
            return
        }
        selectedIndex = min(max(0, selectedIndex), items.count - 1)
    }
}
