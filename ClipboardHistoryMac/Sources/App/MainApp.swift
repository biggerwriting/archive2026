import AppKit
import Foundation

@main
final class MainApp: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem?
    private let appController = AppController()

    static func main() {
        let app = NSApplication.shared
        let delegate = MainApp()
        app.delegate = delegate
        app.setActivationPolicy(.accessory)
        app.run()
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupMenuBar()
        appController.start()
    }

    private func setupMenuBar() {
        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = item.button {
            button.title = "CL"
            button.toolTip = "Clipboard History"
        }

        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "打开历史 (Option+V)", action: #selector(openHistory), keyEquivalent: ""))
        menu.addItem(.separator())
        menu.addItem(NSMenuItem(title: "退出", action: #selector(quit), keyEquivalent: "q"))
        item.menu = menu

        statusItem = item
    }

    @objc
    private func openHistory() {
        appController.showHistoryPanel()
    }

    @objc
    private func quit() {
        NSApplication.shared.terminate(nil)
    }
}
