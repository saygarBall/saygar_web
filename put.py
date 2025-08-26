import wx
import subprocess
import os

class GitUploader(wx.Frame):
    def __init__(self, parent, title):
        super(GitUploader, self).__init__(parent, title=title, size=(850, 600))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Input paths
        hbox_paths = wx.BoxSizer(wx.HORIZONTAL)
        hbox_paths.Add(wx.StaticText(panel, label="Files/Folders:"), flag=wx.RIGHT, border=8)
        self.paths_input = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        hbox_paths.Add(self.paths_input, proportion=1)
        vbox.Add(hbox_paths, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Browse buttons
        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.browse_file_btn = wx.Button(panel, label="Browse Files")
        self.browse_file_btn.Bind(wx.EVT_BUTTON, self.on_browse_files)
        hbox_buttons.Add(self.browse_file_btn, flag=wx.RIGHT, border=5)

        self.browse_folder_btn = wx.Button(panel, label="Browse Folders")
        self.browse_folder_btn.Bind(wx.EVT_BUTTON, self.on_browse_folders)
        hbox_buttons.Add(self.browse_folder_btn, flag=wx.RIGHT, border=5)
        vbox.Add(hbox_buttons, flag=wx.LEFT|wx.TOP, border=10)

        # Commit message edit box
        hbox_commit = wx.BoxSizer(wx.HORIZONTAL)
        hbox_commit.Add(wx.StaticText(panel, label="Commit Msg (Edit if needed):"), flag=wx.RIGHT, border=8)
        self.commit_input = wx.TextCtrl(panel)
        hbox_commit.Add(self.commit_input, proportion=1)
        vbox.Add(hbox_commit, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Buttons for Git actions
        hbox_actions = wx.BoxSizer(wx.HORIZONTAL)
        self.upload_btn = wx.Button(panel, label="Upload to GitHub")
        self.upload_btn.Bind(wx.EVT_BUTTON, self.on_upload)
        hbox_actions.Add(self.upload_btn, flag=wx.RIGHT, border=5)

        self.stash_btn = wx.Button(panel, label="Stash Changes")
        self.stash_btn.Bind(wx.EVT_BUTTON, self.on_stash)
        hbox_actions.Add(self.stash_btn, flag=wx.RIGHT, border=5)

        self.commit_local_btn = wx.Button(panel, label="Commit Local Changes")
        self.commit_local_btn.Bind(wx.EVT_BUTTON, self.on_commit_local)
        hbox_actions.Add(self.commit_local_btn, flag=wx.RIGHT, border=5)

        self.discard_btn = wx.Button(panel, label="Discard Local Changes")
        self.discard_btn.Bind(wx.EVT_BUTTON, self.on_discard)
        hbox_actions.Add(self.discard_btn)
        vbox.Add(hbox_actions, flag=wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, border=10)

        # Log box (Read-only)
        self.log_box = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY)
        vbox.Add(self.log_box, proportion=2, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

    def run_cmd(self, cmd):
        """รันคำสั่ง shell และโชว์ log"""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            self.log_box.AppendText(result.stdout + "\n")
        if result.stderr:
            self.log_box.AppendText("Error: " + result.stderr + "\n")
        return result.returncode == 0

    def has_unstaged_changes(self):
        """เช็กว่า git มี unstaged changes หรือไม่"""
        result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
        return bool(result.stdout.strip())

    def check_path_on_remote(self, path, branch="main"):
        """เช็กว่าไฟล์หรือโฟลเดอร์อยู่บน remote GitHub หรือไม่"""
        self.run_cmd("git fetch origin")
        result = subprocess.run(f"git ls-tree -r origin/{branch} --name-only",
                                shell=True, capture_output=True, text=True)
        remote_files = result.stdout.splitlines()

        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    rel_path = os.path.relpath(os.path.join(root, f))
                    if rel_path in remote_files:
                        return True
            return False
        else:
            return path in remote_files

    def on_browse_files(self, event):
        dlg = wx.FileDialog(self, "เลือกหลายไฟล์", "", "", "*.*", wx.FD_OPEN | wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            files = dlg.GetPaths()
            current = self.paths_input.GetValue().splitlines()
            self.paths_input.SetValue("\n".join(current + files))
        dlg.Destroy()

    def on_browse_folders(self, event):
        dlg = wx.DirDialog(self, "เลือกโฟลเดอร์")
        if dlg.ShowModal() == wx.ID_OK:
            current = self.paths_input.GetValue().splitlines()
            self.paths_input.SetValue("\n".join(current + [dlg.GetPath()]))
        dlg.Destroy()

    def on_commit_local(self, event):
        if self.has_unstaged_changes():
            self.run_cmd('git add .')
            self.run_cmd('git commit -m "Save local changes"')
            self.log_box.AppendText("Local changes committed.\n")
        else:
            self.log_box.AppendText("ไม่มี local changes ให้ commit.\n")

    def on_stash(self, event):
        if self.has_unstaged_changes():
            self.run_cmd('git stash')
            self.log_box.AppendText("Local changes stashed.\n")
        else:
            self.log_box.AppendText("ไม่มี local changes ให้ stash.\n")

    def on_discard(self, event):
        if self.has_unstaged_changes():
            self.run_cmd('git reset --hard')
            self.log_box.AppendText("Local changes discarded.\n")
        else:
            self.log_box.AppendText("ไม่มี local changes ให้ discard.\n")

    def on_upload(self, event):
        if self.has_unstaged_changes():
            self.log_box.AppendText("มี local changes ยังไม่ได้ commit! กรุณา commit/stash/discard ก่อน pull.\n")
            return

        paths = [p.strip() for p in self.paths_input.GetValue().splitlines() if p.strip()]
        if not paths:
            wx.MessageBox("กรุณาเลือกไฟล์หรือโฟลเดอร์อย่างน้อย 1 รายการ!", "Error", wx.OK|wx.ICON_ERROR)
            return

        commit_msg = self.commit_input.GetValue().strip()
        auto_msg = "Update: " + ", ".join([os.path.basename(p) for p in paths])
        if not commit_msg:
            commit_msg = auto_msg

        # Pull ก่อน push
        self.log_box.AppendText("Pull ก่อน push...\n")
        pull_success = self.run_cmd("git pull origin main --rebase")
        if not pull_success:
            self.log_box.AppendText("เกิดข้อผิดพลาดระหว่าง pull! โปรดแก้ conflict ก่อน.\n")
            return

        for path in paths:
            if not os.path.exists(path):
                self.log_box.AppendText(f"ไฟล์/โฟลเดอร์ไม่พบบนเครื่อง: {path}\n")
                continue

            if self.check_path_on_remote(path):
                self.log_box.AppendText(f"{path} มีอยู่บน remote → ลบก่อน...\n")
                self.run_cmd(f'git rm -r --cached "{path}"')
            else:
                self.log_box.AppendText(f"{path} ยังไม่มีบน remote\n")

            self.run_cmd(f'git add "{path}"')

        self.run_cmd(f'git commit -m "{commit_msg}"')
        self.log_box.AppendText("Push ขึ้น GitHub...\n")
        push_success = self.run_cmd("git push origin main")
        if push_success:
            self.log_box.AppendText("เรียบร้อย! ไฟล์/โฟลเดอร์ทั้งหมดถูกอัปโหลดแล้ว\n")
        else:
            self.log_box.AppendText("Push ล้มเหลว! โปรดตรวจสอบ conflict หรือสิทธิ์การเข้าถึง\n")

if __name__ == "__main__":
    app = wx.App()
    GitUploader(None, title="Git Multi File/Folder Uploader with Pull & Conflict Handling")
    app.MainLoop()
