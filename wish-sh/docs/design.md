# TUI Design Documentation

This document provides a comprehensive overview of the Text User Interface (TUI) implementation for wish-sh. It is intended for both AI and human contributors to understand the design concepts, architecture, and implementation details.

## 1. Overview

The wish-sh TUI is a terminal-based user interface built using the [Textual](https://textual.textualize.io/) framework. Textual is a modern Python framework for creating rich, responsive terminal applications with a widget-based architecture similar to web applications.

The TUI allows users to:
- Create new wishes (commands to be executed)
- View wish history
- Examine command outputs
- Navigate between different sections of the interface

The application follows a multi-pane layout with keyboard-driven navigation, providing an efficient interface for power users.

## 2. Layout Structure

The TUI is organized into a 2x2 grid layout with four main panes:

```
+------------------+------------------+
|                  |                  |
|                  |                  |
|  WishSelectPane  |     MainPane     |
|                  |                  |
|                  |                  |
+------------------+------------------+
|                  |                  |
|                  |                  |
|  WishSelectPane  |     SubPane      |
|  (continued)     |                  |
|                  |                  |
+------------------+------------------+
                HelpPane
```

### 2.1 Mode-Specific Layout

The MainPane and SubPane are replaced with mode-specific panes depending on the current mode:

```
WISH_HISTORY Mode:
+------------------+------------------------+
|                  |                        |
|                  |                        |
|  WishSelectPane  | WishHistoryMainPane    |
|                  |                        |
|                  |                        |
+------------------+------------------------+
|                  |                        |
|                  |                        |
|  WishSelectPane  | WishHistorySubPane     |
|  (continued)     |                        |
|                  |                        |
+------------------+------------------------+
                HelpPane

NEW_WISH Mode:
+------------------+------------------------+
|                  |                        |
|                  |                        |
|  WishSelectPane  | NewWishMainPane        |
|                  |                        |
|                  |                        |
+------------------+------------------------+
|                  |                        |
|                  |                        |
|  WishSelectPane  | NewWishSubPane         |
|  (continued)     |                        |
|                  |                        |
+------------------+------------------------+
                HelpPane
```

### 2.2 WishSelectPane

- **Location**: Left column, spans both rows
- **Purpose**: Displays a list of past wishes that can be selected
- **Content**: Scrollable list of wish items with status indicators
- **Interaction**: Up/down navigation to select wishes

### 2.3 Mode-Specific Panes

#### 2.3.1 WishHistoryMainPane

- **Location**: Top-right cell in WISH_HISTORY mode
- **Purpose**: Displays details of the selected wish
- **Content**: Wish details and list of commands with their status
- **Interaction**: Up/down navigation to select commands

#### 2.3.2 WishHistorySubPane

- **Location**: Bottom-right cell in WISH_HISTORY mode
- **Purpose**: Displays command output details
- **Content**: Command text, standard output, and standard error
- **Interaction**: Scrollable view with options to view full logs

#### 2.3.3 NewWishMainPane

- **Location**: Top-right cell in NEW_WISH mode
- **Purpose**: Interface for creating a new wish
- **Content**: Forms for wish input, command suggestions, and confirmation
- **Interaction**: Form input and navigation

#### 2.3.4 NewWishSubPane

- **Location**: Bottom-right cell in NEW_WISH mode
- **Purpose**: Provides context for the current new wish state
- **Content**: Guidance messages based on the current state
- **Interaction**: Read-only view

### 2.4 HelpPane


- **Location**: Overlay at the bottom of the screen
- **Purpose**: Provides context-sensitive help information
- **Content**: Available keyboard shortcuts based on the active pane
- **Interaction**: Automatically updates based on the active pane

## 3. Modes

The TUI operates in two distinct modes that affect the behavior and content of the panes:

### 3.1 NEW_WISH Mode

- **Purpose**: Interface for creating a new wish
- **MainPane**: Displays a message indicating new wish creation mode
- **SubPane**: Displays a message indicating where command output will appear
- **Activation**: Default mode when the application starts

### 3.2 WISH_HISTORY Mode

- **Purpose**: Interface for viewing past wishes and their details
- **MainPane**: Displays wish details and a list of commands
- **SubPane**: Displays output of the selected command
- **Activation**: Triggered when a wish is selected from the WishSelectPane

Mode switching is handled by the `set_mode` method in the `MainScreen` class, which updates the content of the panes accordingly.

## 4. Navigation

Navigation in the TUI is primarily keyboard-driven, with the following key bindings:

### 4.1 Pane Navigation

- **Left Arrow**: Focus WishSelectPane
- **Right Arrow**: Focus MainPane
- **Ctrl+Up**: Focus MainPane
- **Ctrl+Down**: Focus SubPane

### 4.2 Content Navigation

- **Up/Down Arrows** or **j/k**: Scroll up/down within the active pane
- **Ctrl+f**: Page down
- **Ctrl+b**: Page up
- **<**: Scroll to top
- **>**: Scroll to bottom

### 4.3 Special Keys

- **o**: View full standard output (when in SubPane)
- **e**: View full standard error (when in SubPane)
- **q**: Confirm quit
- **Ctrl+q**: Quit immediately

### 4.4 Focus Management

The active pane is visually indicated with a lighter background color. When a pane is activated:

1. The `set_active` method is called on the pane
2. The pane receives focus
3. The HelpPane updates to show relevant shortcuts
4. Key events are directed to the active pane

## 5. Event Handling

The TUI uses Textual's event system for handling user interactions:

### 5.1 Key Events

Key events are processed in a hierarchical manner:
1. The application (`WishTUIApp`) receives all key events
2. If a special screen (like `LogViewerScreen`) is active, it gets priority
3. Otherwise, the event is passed to the main screen
4. The main screen checks if the active pane should handle the event
5. If no handler consumes the event, it bubbles back up

### 5.2 Message Passing

Custom messages are used for communication between components:

- **WishSelected**: Sent when a wish is selected in the WishSelectPane
- **CommandSelected**: Sent when a command is selected in the MainPane

These messages trigger updates in other panes, such as displaying command output in the SubPane when a command is selected.

## 6. Styling

The TUI uses CSS-like styling defined in `wish_tui.css`:

### 6.1 Layout Styling

- Grid layout with specific dimensions for each pane
- WishSelectPane has a fixed width of 30 characters
- MainPane and SubPane expand to fill available space

### 6.2 Visual Feedback

- Active panes have a lighter background color
- Selected items have a darker accent background and different text color
- Command status is indicated with different colors (success, warning, error)

### 6.3 Text Formatting

- Rich markup is used for text formatting (bold, colors)
- Special handling is required for text that contains markup characters

## 7. Special Screens

In addition to the main screen, the TUI includes special screens for specific purposes:

### 7.1 LogViewerScreen

- **Purpose**: Displays full log content in a modal dialog
- **Activation**: Triggered by pressing 'o' or 'e' in the SubPane
- **Features**: Scrollable view with line count and navigation controls

### 7.2 QuitScreen

- **Purpose**: Confirmation dialog for quitting the application
- **Activation**: Triggered by pressing 'q'
- **Features**: Yes/No buttons for confirming the action

## 8. Best Practices

The TUI implementation follows several best practices:

### 8.1 Code Organization

- Separation of concerns with distinct classes for each pane
- Base class (`BasePane`) for common functionality
- Clear hierarchy of components

### 8.2 Logging

- Consistent logging throughout the application
- Debug logs for tracking events and state changes
- Configurable log level via environment variable

### 8.3 Safe Text Handling

- Proper escaping of markup characters in user-generated content
- Sanitization of command text to prevent display issues
- Handling of edge cases (None values, empty strings)

### 8.4 Error Handling

- Graceful handling of exceptions
- Informative error messages
- Fallback mechanisms for recovering from errors

## 9. Implementation Details

### 9.1 Key Classes

- **WishTUIApp**: Main application class
- **MainScreen**: Primary screen containing the panes
- **BasePane**: Base class for all panes
- **WishSelectPane**: Left pane for wish selection
- **HelpPane**: Bottom overlay for help text

#### 9.1.1 Mode-Specific Panes

The application uses mode-specific panes to separate concerns based on the current mode:

- **WishHistoryMainPane**: Top-right pane for wish history details
- **WishHistorySubPane**: Bottom-right pane for command output in history mode
- **NewWishMainPane**: Top-right pane for new wish creation
- **NewWishSubPane**: Bottom-right pane for new wish command output

#### 9.1.2 Composite Pattern

The application uses the Composite pattern to manage mode-specific panes:

```
                  ┌───────────────┐
                  │ PaneComposite │
                  │   (Abstract)  │
                  └───────┬───────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
┌───────────▼───────────┐   ┌───────────▼───────────┐
│ WishHistoryPaneComposite│   │  NewWishPaneComposite │
└───────────┬───────────┘   └───────────┬───────────┘
            │                           │
    ┌───────┴────────┐         ┌───────┴────────┐
    │                │         │                │
┌───▼───┐        ┌───▼───┐ ┌───▼───┐        ┌───▼───┐
│WishHist│        │WishHist│ │NewWish│        │NewWish│
│oryMain │        │orySub  │ │Main   │        │Sub    │
│Pane    │        │Pane    │ │Pane   │        │Pane   │
└────────┘        └────────┘ └───────┘        └───────┘
```

- **PaneComposite**: Abstract base class for pane composites
- **WishHistoryPaneComposite**: Manages WishHistoryMainPane and WishHistorySubPane
- **NewWishPaneComposite**: Manages NewWishMainPane and NewWishSubPane

This pattern allows for:
- Encapsulation of mode-specific behavior
- Cleaner mode switching logic
- Better separation of concerns
- Improved testability

### 9.2 Mode Switching

The MainScreen class manages mode switching by:

1. Hiding all panes
2. Showing the appropriate mode-specific panes
3. Setting the active composite
4. Delegating to the active composite for mode-specific updates

This approach provides a clean separation between different modes and makes it easier to add new modes in the future.

### 9.3 Utility Functions

- **make_markup_safe**: Safely escapes markup characters
- **sanitize_command_text**: Replaces problematic characters in command text
- **setup_logger**: Configures logging with appropriate levels

## 10. Future Improvements

Potential areas for enhancement:

- Color theme customization
- Mouse support for navigation
- Search functionality for wish history
- Keyboard shortcut customization
- Responsive layout for different terminal sizes
