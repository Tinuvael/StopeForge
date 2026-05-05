import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Any, Callable

from db.connection import DEFAULT_PROJECT_DB_PATH
from db.project_repository import (
    create_project,
    delete_domain,
    delete_project,
    get_domain,
    list_domains,
    list_projects,
    sync_projects_and_domains_from_case_histories,
    upsert_domain,
)


STANDARD_SURFACES = [
    "Crown",
    "Hanging wall",
    "Footwall",
    "End wall",
]


class DomainEditor(tk.Toplevel):
    def __init__(self, parent, project_id: int, domain: dict[str, Any] | None, on_saved: Callable[[], None]):
        super().__init__(parent)

        self.project_id = project_id
        self.domain = domain or {}
        self.on_saved = on_saved

        self.title("Domain properties")
        self.geometry("760x720")
        self.minsize(700, 650)

        self.vars: dict[str, tk.StringVar] = {}

        self._build_ui()

    def _make_var(self, field: str) -> tk.StringVar:
        value = self.domain.get(field, "")
        var = tk.StringVar(value="" if value is None else str(value))
        self.vars[field] = var
        return var

    def _add_entry(self, parent, row: int, label: str, field: str, width: int = 18):
        ttk.Label(parent, text=label).grid(row=row, column=0, padx=6, pady=4, sticky="w")
        ttk.Entry(parent, textvariable=self._make_var(field), width=width).grid(
            row=row,
            column=1,
            padx=6,
            pady=4,
            sticky="w",
        )

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        row = 0

        ttk.Label(
            container,
            text="Domain properties",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=row, column=0, columnspan=4, sticky="w", pady=(0, 10))
        row += 1

        ttk.Label(container, text="Domain name").grid(row=row, column=0, padx=6, pady=4, sticky="w")
        ttk.Entry(
            container,
            textvariable=self._make_var("domain_name"),
            width=32,
        ).grid(row=row, column=1, padx=6, pady=4, sticky="w")
        row += 1

        rock_frame = ttk.LabelFrame(container, text="Basic rock mass and stress parameters")
        rock_frame.grid(row=row, column=0, columnspan=4, sticky="we", pady=8)
        row += 1

        self._add_entry(rock_frame, 0, "Mining depth, m", "mining_depth_m")
        self._add_entry(rock_frame, 1, "Unit weight, t/m³", "unit_weight_t_m3")
        self._add_entry(rock_frame, 2, "UCS, MPa", "ucs_mpa")
        self._add_entry(rock_frame, 3, "Horizontal stress ratio K / λ", "horizontal_stress_ratio")

        orebody_frame = ttk.LabelFrame(container, text="Orebody parameters")
        orebody_frame.grid(row=row, column=0, columnspan=4, sticky="we", pady=8)
        row += 1

        self._add_entry(orebody_frame, 0, "Orebody dip direction, °", "orebody_dip_direction_deg")
        self._add_entry(orebody_frame, 1, "Orebody dip angle, °", "orebody_dip_angle_deg")
        self._add_entry(orebody_frame, 2, "Orebody thickness, m", "orebody_thickness_m")

        q_frame = ttk.LabelFrame(container, text="Q′ values")
        q_frame.grid(row=row, column=0, columnspan=4, sticky="we", pady=8)
        row += 1

        self._add_entry(q_frame, 0, "Default Q′", "q_prime_default")
        self._add_entry(q_frame, 1, "Crown Q′", "q_prime_crown")
        self._add_entry(q_frame, 2, "Hanging wall Q′", "q_prime_hanging_wall")
        self._add_entry(q_frame, 3, "Footwall Q′", "q_prime_footwall")
        self._add_entry(q_frame, 4, "End wall Q′", "q_prime_end_wall")

        joint_frame = ttk.LabelFrame(container, text="Joint sets")
        joint_frame.grid(row=row, column=0, columnspan=4, sticky="we", pady=8)
        row += 1

        ttk.Label(joint_frame, text="Set").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        ttk.Label(joint_frame, text="Dip, °").grid(row=0, column=1, padx=6, pady=4, sticky="w")
        ttk.Label(joint_frame, text="Dip direction, °").grid(row=0, column=2, padx=6, pady=4, sticky="w")

        for index in range(1, 6):
            ttk.Label(joint_frame, text=f"Set {index}").grid(row=index, column=0, padx=6, pady=4, sticky="w")
            ttk.Entry(
                joint_frame,
                textvariable=self._make_var(f"joint{index}_dip_deg"),
                width=14,
            ).grid(row=index, column=1, padx=6, pady=4, sticky="w")
            ttk.Entry(
                joint_frame,
                textvariable=self._make_var(f"joint{index}_dip_direction_deg"),
                width=14,
            ).grid(row=index, column=2, padx=6, pady=4, sticky="w")

        comment_frame = ttk.LabelFrame(container, text="Comment")
        comment_frame.grid(row=row, column=0, columnspan=4, sticky="we", pady=8)
        row += 1

        ttk.Entry(
            comment_frame,
            textvariable=self._make_var("comment"),
            width=90,
        ).grid(row=0, column=0, padx=6, pady=6, sticky="we")

        button_frame = ttk.Frame(container)
        button_frame.grid(row=row, column=0, columnspan=4, sticky="e", pady=(12, 0))

        ttk.Button(button_frame, text="Save", command=self.save).pack(side="right", padx=6)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="right", padx=6)

    def save(self):
        row = {
            "project_id": self.project_id,
        }

        for field, var in self.vars.items():
            row[field] = var.get().strip()

        try:
            upsert_domain(row, db_path=DEFAULT_PROJECT_DB_PATH)
        except Exception as error:
            messagebox.showerror("Save domain error", str(error))
            return

        self.on_saved()
        self.destroy()


class ProjectTreePanel(ttk.Frame):
    def __init__(self, parent, on_context_changed: Callable[[dict[str, str]], None] | None = None):
        super().__init__(parent)

        self.on_context_changed = on_context_changed
        self.item_context: dict[str, dict[str, Any]] = {}

        self._build_ui()
        self.refresh_tree()

    def _build_ui(self):
        title_frame = ttk.Frame(self)
        title_frame.pack(fill="x", padx=6, pady=(6, 2))

        ttk.Label(
            title_frame,
            text="Project Tree",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left")

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=6, pady=6)

        self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=6, pady=(0, 6))

        ttk.Button(button_frame, text="Add project", command=self.add_project).pack(fill="x", pady=2)
        ttk.Button(button_frame, text="Add domain", command=self.add_domain).pack(fill="x", pady=2)
        ttk.Button(button_frame, text="Edit domain", command=self.edit_domain).pack(fill="x", pady=2)
        ttk.Button(button_frame, text="Delete selected", command=self.delete_selected).pack(fill="x", pady=2)
        ttk.Button(button_frame, text="Sync from case histories", command=self.sync_from_case_histories,).pack(fill="x", pady=2)
        ttk.Button(button_frame, text="Refresh", command=self.refresh_tree).pack(fill="x", pady=2)

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.item_context.clear()

        projects = list_projects(DEFAULT_PROJECT_DB_PATH)

        for project in projects:
            project_item = self.tree.insert(
                "",
                "end",
                text=project["project_name"],
                open=True,
            )

            self.item_context[project_item] = {
                "node_type": "project",
                "project_id": project["id"],
                "project": project["project_name"],
                "domain_id": None,
                "domain": "",
                "surface": "",
            }

            domains = list_domains(project_id=project["id"], db_path=DEFAULT_PROJECT_DB_PATH)

            for domain in domains:
                domain_item = self.tree.insert(
                    project_item,
                    "end",
                    text=domain["domain_name"],
                    open=True,
                )

                self.item_context[domain_item] = {
                    "node_type": "domain",
                    "project_id": project["id"],
                    "project": project["project_name"],
                    "domain_id": domain["id"],
                    "domain": domain["domain_name"],
                    "surface": "",
                }

                for surface in STANDARD_SURFACES:
                    surface_item = self.tree.insert(
                        domain_item,
                        "end",
                        text=surface,
                        open=False,
                    )

                    self.item_context[surface_item] = {
                        "node_type": "surface",
                        "project_id": project["id"],
                        "project": project["project_name"],
                        "domain_id": domain["id"],
                        "domain": domain["domain_name"],
                        "surface": surface,
                    }

    def get_selected_context(self) -> dict[str, Any] | None:
        selection = self.tree.selection()

        if not selection:
            return None

        return self.item_context.get(selection[0])

    def on_select(self, _event=None):
        context = self.get_selected_context()

        if context is None:
            return

        if self.on_context_changed is not None:
            self.on_context_changed(context)

    def add_project(self):
        project_name = simpledialog.askstring(
            "Add project",
            "Project / deposit name:",
            parent=self,
        )

        if not project_name:
            return

        try:
            create_project(project_name, db_path=DEFAULT_PROJECT_DB_PATH)
        except Exception as error:
            messagebox.showerror("Add project error", str(error))
            return

        self.refresh_tree()

    def add_domain(self):
        context = self.get_selected_context()

        if context is None:
            messagebox.showinfo("Add domain", "Select a project first.")
            return

        project_id = context.get("project_id")

        if not project_id:
            messagebox.showinfo("Add domain", "Select a project first.")
            return

        DomainEditor(
            self,
            project_id=int(project_id),
            domain=None,
            on_saved=self.refresh_tree,
        )

    def edit_domain(self):
        context = self.get_selected_context()

        if context is None:
            messagebox.showinfo("Edit domain", "Select a domain first.")
            return

        domain_id = context.get("domain_id")
        project_id = context.get("project_id")

        if not domain_id or not project_id:
            messagebox.showinfo("Edit domain", "Select a domain first.")
            return

        domain = get_domain(int(domain_id), db_path=DEFAULT_PROJECT_DB_PATH)

        DomainEditor(
            self,
            project_id=int(project_id),
            domain=domain,
            on_saved=self.refresh_tree,
        )

    def delete_selected(self):
        context = self.get_selected_context()

        if context is None:
            return

        node_type = context.get("node_type")

        if node_type == "surface":
            messagebox.showinfo("Delete selected", "Surfaces are generated automatically and cannot be deleted.")
            return

        if node_type == "domain":
            answer = messagebox.askyesno(
                "Delete domain",
                f"Delete domain '{context.get('domain')}'?",
            )

            if not answer:
                return

            delete_domain(int(context["domain_id"]), db_path=DEFAULT_PROJECT_DB_PATH)
            self.refresh_tree()
            return

        if node_type == "project":
            answer = messagebox.askyesno(
                "Delete project",
                f"Delete project '{context.get('project')}' and all its domains?",
            )

            if not answer:
                return

            delete_project(int(context["project_id"]), db_path=DEFAULT_PROJECT_DB_PATH)
            self.refresh_tree()

    def sync_from_case_histories(self):
        try:
            result = sync_projects_and_domains_from_case_histories(
                db_path=DEFAULT_PROJECT_DB_PATH,
            )
        except Exception as error:
            messagebox.showerror("Sync error", str(error))
            return

        self.refresh_tree()

        messagebox.showinfo(
            "Sync complete",
            "Project Tree was synchronized from Case Histories.\n\n"
            f"Created projects: {result['created_projects']}\n"
            f"Created domains: {result['created_domains']}\n"
            f"Skipped rows: {result['skipped_rows']}",
        )

    def clear_selection(self):
        self.tree.selection_remove(self.tree.selection())


    def select_context(self, context: dict | None):
        self.clear_selection()

        if not context:
            return

        target_project = context.get("project", "")
        target_domain = context.get("domain", "")
        target_surface = context.get("surface", "")

        if not target_project:
            return

        for item_id, item_context in self.item_context.items():
            if item_context.get("project", "") != target_project:
                continue

            if item_context.get("domain", "") != target_domain:
                continue

            if item_context.get("surface", "") != target_surface:
                continue

            self.tree.selection_set(item_id)
            self.tree.see(item_id)
            return
