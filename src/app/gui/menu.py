from src.app.gui.action.command import (
    CommonAction,
    create_copy_items_to_clipboard_action,
    create_paste_items_from_clipboard_action,
    create_cut_items_to_clipboard_action,
    create_delete_items_action,
    create_rename_action,
    create_duplicate_action,
    create_view_action,
    create_go_to_action,
    create_go_to_repo_action,
    create_edit_action,
    create_properties_action,
    create_copy_to_action,
    create_move_to_action,
)
from src.app.gui.action.file import (
    FileAction,
    create_open_file_action,
    create_file_action,
    create_file_from_clipboard_text_action,
)
from src.app.gui.action.folder import (
    FolderAction,
    create_folder_action,
    create_select_folder_action,
    create_pin_action,
    create_open_folder_externally_action,
    create_open_folder_in_new_tab_action,
    create_open_console_action,
    create_select_folder_in_new_tab_action,
)
from src.app.gui.action.selection import (
    SelectionAction,
    create_copy_path_action,
    create_copy_path_with_name_action,
    create_copy_name_action,
)
from src.app.gui.action.tab import (
    create_new_tab_action,
    TabAction,
    create_close_tab_action,
    create_close_all_tabs_action,
)


def init_menu(main_form):
    init_file_menu(main_form)
    init_folder_menu(main_form)
    init_command_menu(main_form)
    init_selection_menu(main_form)
    init_tab_menu(main_form)
    init_view_menu(main_form)


def init_file_menu(main_form):
    file_menu = main_form.menuBar().addMenu("&File")
    # Create
    main_form.actions[FileAction.CREATE] = create_file_action(parent=main_form, path_func=main_form.path_func)
    file_menu.addAction(main_form.actions[FileAction.CREATE])
    # Open
    main_form.actions[FileAction.OPEN] = create_open_file_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    file_menu.addAction(main_form.actions[FileAction.OPEN])
    # Create from clipboard text
    main_form.actions[FileAction.CREATE_CLIP] = create_file_from_clipboard_text_action(
        parent=main_form, path_func=main_form.path_func
    )
    file_menu.addAction(main_form.actions[FileAction.CREATE_CLIP])
    # Open file in VS code


def init_folder_menu(main_form):
    folder_menu = main_form.menuBar().addMenu("Fol&der")
    # Create
    main_form.actions[FolderAction.CREATE] = create_folder_action(parent=main_form, path_func=main_form.path_func)
    folder_menu.addAction(main_form.actions[FolderAction.CREATE])
    # Select current
    folder_menu.addSeparator()
    main_form.actions[FolderAction.SELECT] = create_select_folder_action(parent_func=main_form.current_tree)
    folder_menu.addAction(main_form.actions[FolderAction.SELECT])
    # Select in new tab
    main_form.actions[FolderAction.SELECT_IN_NEW_TAB] = create_select_folder_in_new_tab_action(
        parent_func=main_form.current_tree
    )
    folder_menu.addAction(main_form.actions[FolderAction.SELECT_IN_NEW_TAB])
    # Pin
    main_form.actions[FolderAction.PIN] = create_pin_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func, pin=True
    )
    folder_menu.addAction(main_form.actions[FolderAction.PIN])
    # Unpin
    main_form.actions[FolderAction.UNPIN] = create_pin_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func, pin=False
    )
    folder_menu.addAction(main_form.actions[FolderAction.UNPIN])
    # Open (externally)
    folder_menu.addSeparator()
    main_form.actions[FolderAction.OPEN_EXT] = create_open_folder_externally_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    folder_menu.addAction(main_form.actions[FolderAction.OPEN_EXT])
    # Open (new tab)
    main_form.actions[FolderAction.OPEN_TAB] = create_open_folder_in_new_tab_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    folder_menu.addAction(main_form.actions[FolderAction.OPEN_TAB])

    # Open (new window)
    # Open (VS Code)
    # Open Console
    main_form.actions[FolderAction.OPEN_CONSOLE] = create_open_console_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    folder_menu.addAction(main_form.actions[FolderAction.OPEN_CONSOLE])


def init_command_menu(main_form):
    command_menu = main_form.menuBar().addMenu("&Command")
    # Go to
    main_form.actions[CommonAction.GO_TO] = create_go_to_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.GO_TO])
    # Go to repo
    main_form.actions[CommonAction.GO_TO_REPO] = create_go_to_repo_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.GO_TO_REPO])
    # Cut
    command_menu.addSeparator()
    main_form.actions[CommonAction.CUT] = create_cut_items_to_clipboard_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.CUT])
    # Copy
    main_form.actions[CommonAction.COPY] = create_copy_items_to_clipboard_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.COPY])
    # Paste
    main_form.actions[CommonAction.PASTE] = create_paste_items_from_clipboard_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.PASTE])
    # Rename
    command_menu.addSeparator()
    main_form.actions[CommonAction.RENAME] = create_rename_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.RENAME])
    # View
    main_form.actions[CommonAction.VIEW] = create_view_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.VIEW])
    # Edit
    main_form.actions[CommonAction.EDIT] = create_edit_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.EDIT])
    # Duplicate
    main_form.actions[CommonAction.DUPLICATE] = create_duplicate_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.DUPLICATE])
    # Copy to
    main_form.actions[CommonAction.COPY_TO] = create_copy_to_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.COPY_TO])
    # Move to
    main_form.actions[CommonAction.MOVE_TO] = create_move_to_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.MOVE_TO])
    # Compare
    # Properties
    main_form.actions[CommonAction.PROPERTIES] = create_properties_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.PROPERTIES])
    # Delete
    command_menu.addSeparator()
    main_form.actions[CommonAction.DELETE] = create_delete_items_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    command_menu.addAction(main_form.actions[CommonAction.DELETE])


def init_selection_menu(main_form):
    selection_menu = main_form.menuBar().addMenu("&Selection")
    # Copy path
    main_form.actions[SelectionAction.COPY_PATH] = create_copy_path_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    selection_menu.addAction(main_form.actions[SelectionAction.COPY_PATH])
    # Copy path with name
    main_form.actions[SelectionAction.COPY_PATH_WITH_NAME] = create_copy_path_with_name_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    selection_menu.addAction(main_form.actions[SelectionAction.COPY_PATH_WITH_NAME])
    # Copy name
    main_form.actions[SelectionAction.COPY_NAME] = create_copy_name_action(
        parent_func=main_form.current_tree, path_func=main_form.path_func
    )
    selection_menu.addAction(main_form.actions[SelectionAction.COPY_NAME])
    #  -----------
    # Select children/siblings
    # Invert selection


def init_tab_menu(main_form):
    tab_menu = main_form.menuBar().addMenu("&Tab")
    # New
    main_form.actions[TabAction.NEW] = create_new_tab_action(parent=main_form.tree_box)
    tab_menu.addAction(main_form.actions[TabAction.NEW])
    # Close all
    tab_menu.addSeparator()
    main_form.actions[TabAction.CLOSE_ALL] = create_close_all_tabs_action(parent_func=lambda: main_form.tree_box)
    tab_menu.addAction(main_form.actions[TabAction.CLOSE_ALL])
    # Close
    main_form.actions[TabAction.CLOSE] = create_close_tab_action(
        parent_func=lambda: main_form.tree_box, index_func=main_form.tree_box.currentIndex
    )
    tab_menu.addAction(main_form.actions[TabAction.CLOSE])


def init_view_menu(main_form):
    view_menu = main_form.menuBar().addMenu("&View")
    # show favorite
    # show buttons
    # file filter
    # always on top
