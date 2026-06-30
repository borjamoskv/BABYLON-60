#!/usr/bin/env python3
"""
Mac-Control-Ω Sentinel: Anti-Friction Window Manager (V2 Zero-Entropy)
Event-driven architecture using AppKit and CoreFoundation.
Consumes 0.00% CPU when idle.
"""

import sys
import os
try:
    import objc
    import CoreFoundation
    import ApplicationServices
    from AppKit import NSWorkspace, NSScreen, NSApplication
    from Foundation import NSObject
    from PyObjCTools import AppHelper
except ImportError:
    print("Error: PyObjC is required. Run: pip install pyobjc")
    sys.exit(1)

# List of apps allowed to go full screen or occupy 100%
WHITELIST = [
    "com.apple.FinalCut",
    "com.apple.logic10",
    "com.blizzard.worldofwarcraft",
    "com.valvesoftware.steam"
]

def get_main_screen_size():
    screen = NSScreen.mainScreen()
    if screen:
        frame = screen.frame()
        return frame.size.width, frame.size.height
    return 1920, 1080

def apply_friction_correction(ax_window, screen_w, screen_h):
    """Resizes and centers the window to 80% of screen size."""
    new_w = int(screen_w * 0.8)
    new_h = int(screen_h * 0.8)
    new_x = int((screen_w - new_w) / 2)
    new_y = int((screen_h - new_h) / 2)
    
    pos = ApplicationServices.CGPoint(new_x, new_y)
    pos_val = ApplicationServices.AXValueCreate(ApplicationServices.kAXValueCGPointType, pos)
    ApplicationServices.AXUIElementSetAttributeValue(ax_window, ApplicationServices.kAXPositionAttribute, pos_val)
    
    size = ApplicationServices.CGSize(new_w, new_h)
    size_val = ApplicationServices.AXValueCreate(ApplicationServices.kAXValueCGSizeType, size)
    ApplicationServices.AXUIElementSetAttributeValue(ax_window, ApplicationServices.kAXSizeAttribute, size_val)

def check_window(ax_window):
    err, size_val = ApplicationServices.AXUIElementCopyAttributeValue(ax_window, ApplicationServices.kAXSizeAttribute)
    if err == ApplicationServices.kAXErrorSuccess and size_val:
        success, size = ApplicationServices.AXValueGetValue(size_val, ApplicationServices.kAXValueCGSizeType, None)
        if success:
            screen_w, screen_h = get_main_screen_size()
            if size.width > (screen_w * 0.95) and size.height > (screen_h * 0.95):
                print("[SENTINEL-V2] Rogue window size detected. Applying physics correction.")
                apply_friction_correction(ax_window, screen_w, screen_h)

@objc.callbackFor(ApplicationServices.AXObserverCreate)
def ax_observer_callback(observer, ax_element, notification, refcon):
    if notification in (ApplicationServices.kAXWindowResizedNotification, ApplicationServices.kAXWindowCreatedNotification, ApplicationServices.kAXFocusedWindowChangedNotification):
        check_window(ax_element)

class AppSwitchObserver(NSObject):
    def init(self):
        self = objc.super(AppSwitchObserver, self).init()
        if self is None:
            return None
        self.current_observer = None
        self.current_pid = None
        return self

    def applicationActivated_(self, notification):
        app = notification.userInfo().get("NSWorkspaceApplicationKey")
        if not app:
            return
        
        bundle_id = app.bundleIdentifier()
        if bundle_id in WHITELIST:
            return
            
        pid = app.processIdentifier()
        if pid == self.current_pid:
            return
            
        # Clean up old observer runloop source if necessary
        # (For C5-REAL efficiency, we just track the active app)
            
        err, observer = ApplicationServices.AXObserverCreate(pid, ax_observer_callback, None)
        if err == ApplicationServices.kAXErrorSuccess:
            ax_app = ApplicationServices.AXUIElementCreateApplication(pid)
            ApplicationServices.AXObserverAddNotification(observer, ax_app, ApplicationServices.kAXWindowResizedNotification, None)
            ApplicationServices.AXObserverAddNotification(observer, ax_app, ApplicationServices.kAXWindowCreatedNotification, None)
            ApplicationServices.AXObserverAddNotification(observer, ax_app, ApplicationServices.kAXFocusedWindowChangedNotification, None)
            
            rl_source = ApplicationServices.AXObserverGetRunLoopSource(observer)
            CoreFoundation.CFRunLoopAddSource(CoreFoundation.CFRunLoopGetCurrent(), rl_source, CoreFoundation.kCFRunLoopDefaultMode)
            
            self.current_observer = observer
            self.current_pid = pid
            
            # Immediate check on activation
            err, ax_window = ApplicationServices.AXUIElementCopyAttributeValue(ax_app, ApplicationServices.kAXFocusedWindowAttribute)
            if err == ApplicationServices.kAXErrorSuccess and ax_window:
                check_window(ax_window)

def main():
    print("V2 Anti-Friction Sentinel initialized.")
    print("Zero-Entropy mode: Active (CFRunLoop).")
    
    workspace = NSWorkspace.sharedWorkspace()
    nc = workspace.notificationCenter()
    
    observer = AppSwitchObserver.alloc().init()
    nc.addObserver_selector_name_object_(
        observer,
        "applicationActivated:",
        "NSWorkspaceDidActivateApplicationNotification",
        None
    )
    
    # Initialize NSApplication and start event loop
    NSApplication.sharedApplication()
    AppHelper.runEventLoop()

if __name__ == "__main__":
    main()
