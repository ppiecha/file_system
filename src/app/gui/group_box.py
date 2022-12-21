from typing import Optional, List, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QSplitter, QMenu, QInputDialog, QLineEdit, QMessageBox

from src.app.gui.action.group import create_new_group_action, create_close_group_action, create_rename_group_action
from src.app.gui.favorite_view import FavoriteTree
from src.app.gui.tree_box import TreeBox
from src.app.gui.widget import populated_box_layout, TabWidget
from src.app.model.schema import App, Group
from src.app.utils.constant import APP_NAME


class GroupPanel(QWidget):
    def __init__(self, parent: QWidget, app: App, group: Group):
        super().__init__(parent)
        self.app = app
        self.group = group
        self.splitter = QSplitter(self)
        self.favorite_tree = FavoriteTree(parent=self.splitter, group=group)
        self.tree_box = TreeBox(parent=self.splitter, group=group)
        self.splitter.addWidget(self.favorite_tree)
        self.splitter.addWidget(self.tree_box)

        if group.splitter_sizes:
            self.splitter.setSizes(group.splitter_sizes)
        self.splitter.splitterMoved.connect(self.on_splitter_moved)

        self.setLayout(populated_box_layout(widgets=[self.splitter]))

    def on_splitter_moved(self, pos, index):
        self.group.splitter_sizes = self.splitter.sizes()


class GroupBox(TabWidget):
    def __init__(self, parent, app_model: App):
        super().__init__(parent=parent)
        self.main_form = parent
        self.app_model = app_model
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        self.currentChanged.connect(self.on_current_changed)
        self.open_groups()

    def get_all_groups_panels(self) -> List[GroupPanel]:
        result = []
        for index in range(self.count()):
            result.append(self.widget(index))
        return result

    def save_pinned_paths(self):
        for panel in self.get_all_groups_panels():
            current_tree = panel.tree_box.current_tree()
            path = current_tree.pinned_path if current_tree else None
            panel.group.last_page_pinned_path = path

    def store_groups_layout(self):
        for panel in self.get_all_groups_panels():
            panel.tree_box.store_pages_layout()

    def current_group_panel(self) -> Optional[GroupPanel]:
        index = self.currentIndex()
        if index < 0:
            return None
        return self.widget(index)

    def get_name(self, group: Group) -> Group:
        group = group.copy(deep=True)
        text, ok = QInputDialog.getText(self, "", "Enter name", QLineEdit.Normal, text=group.name)
        if ok:
            if self.is_group_name_valid(old_name=group.name, new_name=text):
                group.name = text
            else:
                QMessageBox.information(self, APP_NAME, "Group name is not valid")
        return group

    def is_group_name_valid(self, old_name: str, new_name: str) -> bool:
        if old_name == new_name:
            return True
        if new_name == "":
            return False
        lookup = [panel for panel in self.get_all_groups_panels() if panel.group.name == new_name]
        return len(lookup) == 0

    def new_group(self):
        group = Group()
        group = self.get_name(group=group)
        if group.name:
            self.app_model.groups.append(group)
            group_panel = self.add_group(group=group)
            group_panel.tree_box.open_root_page(find_existing=True)
            self.go_to_group(group=group)

    def rename_group(self):
        group = self.current_group_panel().group
        changed_group = self.get_name(group=group)
        if changed_group.name != group.name and (index := self.currentIndex()) >= 0:
            group.name = changed_group.name
            self.setTabText(index, changed_group.name)

    def go_to_group(self, group: Group):
        index = self.get_group_index(group=group)
        self.setCurrentIndex(index)

    def open_default_group(self):
        group = Group(name="Default")
        self.app_model.groups.append(group)
        group_panel = self.add_group(group=group)
        self.go_to_group(group=group)
        group_panel.tree_box.open_root_page(find_existing=True)

    def open_groups(self):
        if not self.app_model.groups:
            self.open_default_group()
            return
        for group in self.app_model.groups:
            self.add_group(group=group)
        if self.app_model.last_group and self.app_model.last_group in [group.name for group in self.app_model.groups]:
            self.go_to_group(self.app_model.get_group_by_name(self.app_model.last_group))

    def add_group(self, group: Group) -> GroupPanel:
        group_panel = self.get_group_component(group=group)
        self.addTab(group_panel, group.name)
        return group_panel

    def get_group_component(self, group: Group) -> GroupPanel:
        return GroupPanel(parent=self, app=self.app_model, group=group)

    def get_group_index(self, group: Group) -> int:
        for index in range(self.count()):
            if self.widget(index).group == group:
                return index
        raise ValueError(f"Cannot find group {group.name}")

    def open_menu(self, position):
        menu = QMenu()
        index = self.tabBar().tabAt(position)
        if index >= 0:
            menu.addAction(create_new_group_action(parent=self))
            menu.addAction(create_rename_group_action(parent_func=lambda: self))
            menu.addAction(create_close_group_action(parent_func=lambda: self, index_func=self.currentIndex))
        menu.exec_(self.mapToGlobal(position))

    def on_current_changed(self, index: int):
        pass

    def close_page(self, index_func: Callable):
        index = index_func()
        if index is None or index < 0:
            QMessageBox.information(self.parent(), APP_NAME, f"No group selected {index}")
            return
        page = self.widget(index)
        self.app_model.remove_group(page.group)
        page.deleteLater()
        self.removeTab(index)
        if self.count() == 0:
            self.open_default_group()
