import tkinter as tk
import tkinter.messagebox
import tkinter.simpledialog
from tkinter import ttk


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
    def __init__(self):
        self.settings = {"foo": True, "bar": 1, "baz": "ABC"}

        self.root = tk.Tk()
        self.xscroll = tk.Scrollbar(self.root, orient=tk.HORIZONTAL)
        self.yscroll = tk.Scrollbar(self.root, orient=tk.VERTICAL)
        self.columns = ("Key", "Value", "性别")
        self.table = ttk.Treeview(
            self.root,  # 父容器
            height=10,  # 表格显示的行数,height行
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
                column=column, width=100,
                minwidth=100, anchor=tk.CENTER, )  # 定义列
        self.xscroll.config(command=self.table.xview)
        self.xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.yscroll.config(command=self.table.yview)
        self.yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(fill=tk.BOTH, expand=True)

        self.rightClick_menu = tk.Menu(self.root, tearoff=False)
        self.rightClick_menu.add_command(label="修改数据")
        self.root.bind(
            "<Button-3>", lambda event: self.right_click(event.x_root, event.y_root))
        self.refresh()

    def refresh(self):
        self.table.delete(*self.table.get_children())
        # ↑ 将 TreeView 的数据全部干掉
        for index, data in enumerate(self.settings.items()):
            self.table.insert('', tk.END, values=data)  # 添加数据到末尾

    def get_selected_item(self):
        cur_item = self.table.focus()
        item_values = self.table.item(cur_item, 'values')
        return item_values

    def right_click(self, x, y):
        try:
            selected = self.get_selected_item()
            print(selected)
        except tk.TclError:
            selected = False
        if selected:
            self.rightClick_menu.entryconfig(
                "修改数据", state=tk.NORMAL, command=lambda: self.edit_keyvalue(selected[0], selected[1]))
        else:
            self.rightClick_menu.entryconfig("修改数据", state=tk.DISABLED)
        self.rightClick_menu.post(x, y)

    def edit_keyvalue(self, key, defaultval=None):
        val = self.settings.get(key)
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
        self.settings.update(
            {key: self.settings.get(key) if edit_val is None else edit_val})
        self.refresh()

    def edit_keyvalue_api(self, key, value):
        pass


gui = GUI()
gui.root.mainloop()
