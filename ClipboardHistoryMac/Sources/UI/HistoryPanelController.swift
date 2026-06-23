import AppKit
import SwiftUI

final class HistoryPanelController: NSWindowController, NSWindowDelegate {
    private final class KeyHandlingPanel: NSPanel {
        var onKeyDown: ((NSEvent) -> Void)?

        override func keyDown(with event: NSEvent) {
            onKeyDown?(event)
        }
    }

    private let appController: AppController

    init(appController: AppController) {
        self.appController = appController

        let panel = KeyHandlingPanel(
            contentRect: NSRect(x: 0, y: 0, width: 520, height: 420),
            styleMask: [.titled, .closable],
            backing: .buffered,
            defer: false
        )
        panel.level = .floating
        panel.title = "Clipboard History"
        panel.isReleasedWhenClosed = false
        panel.isMovableByWindowBackground = true

        let view = HistoryPanelView(appController: appController)
        panel.contentViewController = NSHostingController(rootView: view)

        super.init(window: panel)
        panel.delegate = self
        panel.onKeyDown = { [weak self] event in
            self?.handle(event: event)
        }
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    func show() {
        guard let window else { return }
        window.center()
        window.makeKeyAndOrderFront(nil)
    }

    func hide() {
        window?.orderOut(nil)
    }

    func windowWillClose(_ notification: Notification) {
        appController.hideHistoryPanel()
    }

    private func handle(event: NSEvent) {
        switch Int(event.keyCode) {
        case 125: // down arrow
            appController.moveSelectionDown()
        case 126: // up arrow
            appController.moveSelectionUp()
        case 36: // return
            appController.pasteSelectedItem()
        case 53: // esc
            appController.hideHistoryPanel()
        default:
            window?.nextResponder?.keyDown(with: event)
        }
    }
}
