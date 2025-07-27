import json
import tkinter as tk
import tkinter.messagebox
import tkinter.simpledialog
import tkinter.filedialog
from tkinter import ttk
from typing import AnyStr, Sequence, Mapping


class GUI_old:
    def __init__(self):
        self.settings = {"foo": 1, "bar": 1, "baz": 1}
        self.root = tk.Tk()
        self.window = ttk.Treeview(self.root)
        tk.Button(self.root, text="Set foo",
                  command=self.make_callback("foo", 2)).pack()
        tk.Button(self.root, text="Set bar",
                  command=self.make_callback("bar", 2)).pack()
        tk.Button(self.root, text="Set baz",
                  command=self.make_callback("baz", 2)).pack()
        # ...etc

    def make_callback(self, key, val):
        def make_something(*args):
            self.settings[key] = val
            print(self.settings)
        return make_something

    def show_variable(self):
        for k, v in self.settings.items():
            pass


class GUI:
    def __init__(self, config_fp):
        with open(config_fp, "r", encoding="utf-8") as f:
            self.settings = json.loads(f.read())

        self.root = tk.Tk()
        self.xscroll = tk.Scrollbar(self.root, orient=tk.HORIZONTAL)
        self.yscroll = tk.Scrollbar(self.root, orient=tk.VERTICAL)
        self.columns = ("Key", "Value", "Type", "editable")
        self.table = ttk.Treeview(
            self.root,  # 父容器
            height=20,  # 表格显示的行数,height行
            columns=self.columns,  # 显示的列
            show="headings",  # 隐藏首列
            xscrollcommand=self.xscroll.set,  # x轴滚动条
            yscrollcommand=self.yscroll.set,  # y轴滚动条
        )
        for column in self.columns:
            self.table.heading(
                column=column, text=column, anchor=tk.CENTER,
                command=lambda name=column:
                tkinter.messagebox.showinfo('', '{}描述信息~~~'.format(name)))
            self.table.column(
                column=column, width=300,
                minwidth=300, anchor=tk.CENTER, )  # 定义列
        self.xscroll.config(command=self.table.xview)
        self.xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.yscroll.config(command=self.table.yview)
        self.yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(fill=tk.BOTH, expand=True)

        self.rightClick_menu = tk.Menu(self.root, tearoff=False)
        self.rightClick_menu.add_command(label="修改数据")
        self.table.bind(
            "<Button-3>", lambda event: self.right_click(event.x_root, event.y_root))

        # self.root.attributes("-topmost", True)
        self.refresh()

    def refresh(self):
        self.table.delete(*self.table.get_children())
        # ↑ 将 TreeView 的数据全部干掉
        for k, v in self.get_all(self.settings).items():
            self.table.insert("", tk.END, values=(
                k, v, type(v).__name__, self.is_editable(v)))

    def is_editable(self, val):
        return isinstance(val, str | int | float | bool)

    def get_all(self, mapping: Mapping):
        result = dict()
        for k, v in mapping.items():
            if isinstance(v, Mapping):
                for k2, v2 in self.get_all(v).items():
                    result.update({k + "." + k2: v2})
            else:
                result.update({k: v})
        return result

    def get_selected_item(self):
        # 只返回当前正在选择的【键】，不返回对应的值
        cur_item = self.table.focus()
        item_values = self.table.item(cur_item, 'values')
        return item_values[0]

    def right_click(self, x, y):
        try:
            selected = self.get_selected_item()
            print(f"{selected=}")
        except tk.TclError:
            selected = False
        if selected:
            self.rightClick_menu.entryconfig(
                "修改数据", state=tk.NORMAL
                if selected and self.is_editable(self.get_keyvalue_api(self.settings, self.index2indexlist(selected)))
                else tk.DISABLED,
                command=lambda: self.edit_keyvalue(selected, self.get_keyvalue_api(self.settings, self.index2indexlist(selected))))
        else:
            self.rightClick_menu.entryconfig("修改数据", state=tk.DISABLED)
        self.rightClick_menu.post(x, y)

    def index2indexlist(self, index_str: AnyStr):
        print(index_str.split("."))
        return index_str.split(".")

    def edit_keyvalue(self, key: str, defaultval=None):
        val = self.get_keyvalue_api(self.settings, self.index2indexlist(key))
        if isinstance(val, bool):
            edit_val = not val
        elif isinstance(val, int):
            # 注：isinstance(true, int) 会返回 true, 所以 bool 型数据应该为“一等公民”
            edit_val = tkinter.simpledialog.askinteger(
                "修改整型数据", f"{key} =", initialvalue=val)
        elif isinstance(val, float):
            edit_val = tkinter.simpledialog.askfloat(
                "修改浮点型数据", f"{key} =", initialvalue=val)
        elif isinstance(val, str):
            edit_val = tkinter.simpledialog.askstring(
                "修改字符串数据", f"{key} =", initialvalue=val)
        else:
            print(val, type(val))
            edit_val = defaultval
        if edit_val is not None:
            self.set_keyvalue_api(
                self.settings, self.index2indexlist(key), edit_val)
        self.refresh()

    def set_keyvalue_api(self, mapping, key: Sequence, value) -> None:
        # key: str = [foo, bar, baz]
        if len(key) == 1:
            mapping[key[0]] = value
        else:
            self.set_keyvalue_api(
                mapping=mapping[key[0]],
                key=key[1:], value=value
            )

    def get_keyvalue_api(self, mapping, key: Sequence):
        if len(key) == 1:
            return mapping[key[0]]
        else:
            return self.get_keyvalue_api(
                mapping=mapping[key[0]],
                key=key[1:]
            )


if __name__ == "__main__":
    gui = GUI(tkinter.filedialog.askopenfilename(
        filetypes=(("SyncCraft 配置文件", "*.sc_conf"), ("所有文件", "*.*"))))
    tk.Button(gui.root, text="RUN!", bg="yellow",
              width=20, state=tk.DISABLED).pack()
    gui.root.deiconify()
    gui.root.mainloop()
