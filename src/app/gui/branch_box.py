from typing import Optional, List, Tuple

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTabWidget, QWidget, QSplitter, QMenu, QBoxLayout, QInputDialog, QLineEdit, QMessageBox

from src.app.gui.action.group import create_new_group_action
from src.app.gui.favorite_view import FavoriteTree
from src.app.gui.tree_box import TreeBox
from src.app.gui.widget import populated_box_layout
from src.app.model.schema import App, Branch
from src.app.utils.constant import APP_NAME


class BranchPanel(QWidget):
    def __init__(self, parent: QWidget, app: App, branch: Branch):
        super().__init__(parent)
        self.app = app
        self.branch = branch
        self.splitter = QSplitter(self)
        self.favorite_tree = FavoriteTree(parent=self.splitter, branch_model=branch)
        self.tree_box = TreeBox(parent=self.splitter, branch_model=branch)
        self.splitter.addWidget(self.favorite_tree)
        self.splitter.addWidget(self.tree_box)

        if branch.splitter_sizes:
            self.splitter.setSizes(branch.splitter_sizes)
        self.splitter.splitterMoved.connect(self.on_splitter_moved)

        self.setLayout(populated_box_layout(widgets=[self.splitter]))

    def on_splitter_moved(self, pos, index):
        self.branch.splitter_sizes = self.splitter.sizes()


class BranchBox(QTabWidget):
    def __init__(self, parent, app_model: App):
        super().__init__(parent=parent)
        self.main_form = parent
        self.app_model = app_model
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        self.currentChanged.connect(self.on_current_changed)
        self.open_branches()

    def get_all_branch_panels(self) -> List[BranchPanel]:
        result = []
        for index in range(self.count()):
            result.append(self.widget(index))
        return result

    def save_pinned_paths(self):
        for panel in self.get_all_branch_panels():
            current_tree = panel.tree_box.current_tree()
            path = current_tree.pinned_path if current_tree else None
            panel.branch.last_page_pinned_path = path

    def store_branches_layout(self):
        for panel in self.get_all_branch_panels():
            panel.tree_box.store_pages_layout()

    def current_branch_panel(self) -> Optional[BranchPanel]:
        index = self.currentIndex()
        if index < 0:
            return None
        return self.widget(index)

    def get_name(self, branch: Branch) -> Branch:
        text, ok = QInputDialog.getText(self, "", "Enter name", QLineEdit.Normal, text=branch.name)
        if ok:
            if self.is_branch_name_valid(name=text):
                branch.name = text
            else:
                QMessageBox.information(self, APP_NAME, "Group name is not valid")
        return branch

    def is_branch_name_valid(self, name: str) -> bool:
        return True

    def new_group(self):
        branch = Branch()
        branch = self.get_name(branch=branch)
        if branch.name:
            self.app_model.branches.append(branch)
            branch_panel = self.add_branch(branch=branch)
            branch_panel.tree_box.open_root_page()
            self.go_to_branch(branch=branch)

    def rename_group(self):
        pass

    def go_to_branch(self, branch: Branch):
        index = self.get_branch_index(branch=branch)
        self.setCurrentIndex(index)

    def open_branches(self):
        if not self.app_model.branches:
            branch = Branch(name="Default")
            self.app_model.branches.append(branch)
            branch_panel = self.add_branch(branch=branch)
            branch_panel.tree_box.open_root_page()
            return
        for branch in self.app_model.branches:
            self.add_branch(branch=branch)
        if self.app_model.last_branch and self.app_model.last_branch in [
            branch.name for branch in self.app_model.branches
        ]:
            self.go_to_branch(self.app_model.get_branch_by_name(self.app_model.last_branch))

    def add_branch(self, branch: Branch) -> BranchPanel:
        branch_panel = self.get_branch_component(branch=branch)
        self.addTab(branch_panel, branch.name)
        return branch_panel

    def get_branch_component(self, branch: Branch) -> BranchPanel:
        return BranchPanel(parent=self, app=self.app_model, branch=branch)

    def get_branch_index(self, branch: Branch) -> int:
        for index in range(self.count()):
            if self.widget(index).branch == branch:
                return index
        raise ValueError(f"Cannot find branch {branch.name}")

    def open_menu(self, position):
        menu = QMenu()
        index = self.tabBar().tabAt(position)
        if index >= 0:
            menu.addAction(create_new_group_action(parent=self))
            # menu.addAction(create_close_all_tabs_action(parent_func=lambda: self))
        menu.exec_(self.mapToGlobal(position))

    def on_current_changed(self, index: int):
        pass
