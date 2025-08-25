import wx
import sqlite3
import pandas as pd
import os

class SQLExcelConverter(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='SQL <-> Excel Converter', size=(400, 200))
        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.import_btn = wx.Button(panel, label='Import Excel Folder → .db')
        self.export_btn = wx.Button(panel, label='Export .db → Excel Folder')

        vbox.Add(self.export_btn, 0, wx.ALL | wx.EXPAND, 10)
        vbox.Add(self.import_btn, 0, wx.ALL | wx.EXPAND, 10)

        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        self.import_btn.Bind(wx.EVT_BUTTON, self.on_import)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

    def on_export(self, event):
        with wx.FileDialog(self, "เลือกไฟล์ .db", wildcard="SQLite files (*.db)|*.db",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            db_path = fileDialog.GetPath()
            db_name = os.path.splitext(os.path.basename(db_path))[0]
            export_folder = os.path.join(os.path.dirname(db_path), db_name)

            if not os.path.exists(export_folder):
                os.makedirs(export_folder)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # ข้ามตารางระบบ
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
            tables = cursor.fetchall()

            for table_name in tables:
                table = table_name[0]
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                df.to_excel(os.path.join(export_folder, f"{table}.xlsx"), index=False)

            conn.close()
            wx.MessageBox(f'แปลงเป็น Excel เรียบร้อยในโฟลเดอร์:\n{export_folder}', 'Success', wx.OK | wx.ICON_INFORMATION)

    def on_import(self, event):
        with wx.DirDialog(self, "เลือกโฟลเดอร์ที่มีไฟล์ Excel (*.xlsx)", style=wx.DD_DEFAULT_STYLE) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return

            excel_folder = dirDialog.GetPath()

            with wx.FileDialog(self, "บันทึกไฟล์ .db", wildcard="SQLite files (*.db)|*.db",
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as saveDialog:

                if saveDialog.ShowModal() == wx.ID_CANCEL:
                    return

                db_path = saveDialog.GetPath()
                conn = sqlite3.connect(db_path)

                for file in os.listdir(excel_folder):
                    if file.endswith('.xlsx'):
                        table_name = os.path.splitext(file)[0]
                        file_path = os.path.join(excel_folder, file)
                        try:
                            df = pd.read_excel(file_path, dtype=str)

                            # ตรวจจับคอลัมน์เบอร์โทร
                            for col in df.columns:
                                col_lower = col.lower()
                                if any(keyword in col_lower for keyword in ['โทร', 'เบอร์', 'phone', 'tel']):
                                    df[col] = df[col].astype(str).apply(lambda x: f"0{x}" if x.isdigit() and not x.startswith("0") else x)

                            df.to_sql(table_name, conn, if_exists='replace', index=False)
                        except Exception as e:
                            wx.MessageBox(f'เกิดข้อผิดพลาดกับไฟล์ {file}:\n{e}', 'Error', wx.OK | wx.ICON_ERROR)

                conn.close()
                wx.MessageBox('นำเข้าข้อมูลจาก Excel เรียบร้อยแล้ว', 'Success', wx.OK | wx.ICON_INFORMATION)

if __name__ == '__main__':
    app = wx.App(False)
    frame = SQLExcelConverter()
    app.MainLoop()
