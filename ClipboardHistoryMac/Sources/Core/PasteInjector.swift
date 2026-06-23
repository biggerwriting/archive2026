import AppKit
import ApplicationServices
import Carbon.HIToolbox
import Foundation

enum PasteInjectionError: Error {
    case accessibilityPermissionMissing
    case eventCreationFailed
}

final class PasteInjector {
    func isAccessibilityTrusted(promptIfNeeded: Bool) -> Bool {
        let options = [kAXTrustedCheckOptionPrompt.takeRetainedValue() as String: promptIfNeeded] as CFDictionary
        return AXIsProcessTrustedWithOptions(options)
    }

    func paste(text: String) throws {
        guard isAccessibilityTrusted(promptIfNeeded: true) else {
            throw PasteInjectionError.accessibilityPermissionMissing
        }

        let pb = NSPasteboard.general
        pb.clearContents()
        pb.setString(text, forType: .string)

        guard let source = CGEventSource(stateID: .combinedSessionState) else {
            throw PasteInjectionError.eventCreationFailed
        }

        guard
            let keyDown = CGEvent(keyboardEventSource: source, virtualKey: CGKeyCode(kVK_ANSI_V), keyDown: true),
            let keyUp = CGEvent(keyboardEventSource: source, virtualKey: CGKeyCode(kVK_ANSI_V), keyDown: false)
        else {
            throw PasteInjectionError.eventCreationFailed
        }

        keyDown.flags = .maskCommand
        keyUp.flags = .maskCommand
        keyDown.post(tap: .cghidEventTap)
        keyUp.post(tap: .cghidEventTap)
    }
}
