import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np


class VideoApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Video Gaussian Blur Editor")

        # 初始化视频相关的变量
        self.vid = None
        self.frames = []
        self.fps = 0
        self.total_frames = 0
        self.current_frame = 0
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.start_frame = None
        self.end_frame = None
        self.rect_w = 0
        self.rect_h = 0
        self.blurring = False
        self.selecting_start = False
        self.selecting_end = False

        # Tkinter 标签用来显示视频帧
        self.label = tk.Label(window)
        self.label.pack()

        # 显示当前帧和时间的文本框
        self.frame_label = tk.Label(window, text="Frame: 0 / 0, Time: 0.0 sec")
        self.frame_label.pack()

        # 鼠标位置的显示
        self.mouse_position_label = tk.Label(window, text="Mouse Position: X=0, Y=0")
        self.mouse_position_label.pack()

        # 进度条，用来拖动选择帧
        self.progress = tk.Scale(
            window,
            from_=0,
            orient="horizontal",
            length=500,
            command=self.on_progress_change,
        )
        self.progress.pack()

        # 跳转到指定帧的输入框
        self.jump_entry = tk.Entry(window)
        self.jump_entry.pack()

        jump_button = tk.Button(
            window, text="Jump to Frame", command=self.jump_to_frame
        )
        jump_button.pack()

        # 选择起始帧坐标按钮
        self.start_button = tk.Button(
            window,
            text="Select Start Frame Coordinate",
            command=self.select_start_frame,
        )
        self.start_button.pack()

        # 显示起始帧坐标的标签
        self.start_coord_label = tk.Label(
            window, text="Start Coordinate: (X=None, Y=None), Frame: None"
        )
        self.start_coord_label.pack()

        # 选择结束帧坐标按钮
        self.end_button = tk.Button(
            window, text="Select End Frame Coordinate", command=self.select_end_frame
        )
        self.end_button.pack()

        # 显示结束帧坐标的标签
        self.end_coord_label = tk.Label(
            window, text="End Coordinate: (X=None, Y=None), Frame: None"
        )
        self.end_coord_label.pack()

        # 高度和宽度的输入框
        tk.Label(window, text="Blur Width:").pack()
        self.width_entry = tk.Entry(window)
        self.width_entry.pack()

        tk.Label(window, text="Blur Height:").pack()
        self.height_entry = tk.Entry(window)
        self.height_entry.pack()

        # 输入模糊开始帧和结束帧的输入框
        tk.Label(window, text="Start Frame:").pack()
        self.start_frame_entry = tk.Entry(window)
        self.start_frame_entry.pack()

        tk.Label(window, text="End Frame:").pack()
        self.end_frame_entry = tk.Entry(window)
        self.end_frame_entry.pack()

        apply_button = tk.Button(window, text="Apply Blur", command=self.apply_blur)
        apply_button.pack()

        save_button = tk.Button(window, text="Save Video", command=self.save_video)
        save_button.pack()

        # 添加重新选择视频的按钮
        reload_button = tk.Button(
            window, text="Reload Video", command=self.reload_video
        )
        reload_button.pack()

        # 绑定鼠标移动事件，实时显示鼠标坐标
        self.label.bind("<Motion>", self.update_mouse_position)
        self.label.bind("<Button-1>", self.get_coordinates)

        # 绑定键盘事件，使用左右方向键调整帧
        window.bind("<Left>", self.move_left)
        window.bind("<Right>", self.move_right)

        # 初始化并加载视频
        self.load_video()

    def load_video(self):
        """加载视频并初始化相关变量"""
        # 弹出文件选择窗口，用户选择视频文件
        video_source = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=(("Video Files", "*.mp4;*.avi;*.mov"), ("All Files", "*.*")),
        )

        # 如果用户没有选择文件，则退出
        if not video_source:
            print("No file selected.")
            return

        # 打开视频并读取所有帧
        self.vid = cv2.VideoCapture(video_source)
        self.frames.clear()
        self.fps = int(self.vid.get(cv2.CAP_PROP_FPS))
        self.total_frames = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))

        # 读取所有帧
        while True:
            ret, frame = self.vid.read()
            if not ret:
                break
            self.frames.append(frame)

        self.vid.release()

        # 重置状态
        self.current_frame = 0
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.start_frame = None
        self.end_frame = None

        # 更新进度条最大值
        self.progress.config(to=self.total_frames - 1)

        # 更新帧和时间的显示标签
        self.frame_label.config(text=f"Frame: 0 / {self.total_frames}, Time: 0.0 sec")

        # 重置鼠标坐标和帧选择的显示
        self.start_coord_label.config(
            text="Start Coordinate: (X=None, Y=None), Frame: None"
        )
        self.end_coord_label.config(
            text="End Coordinate: (X=None, Y=None), Frame: None"
        )

        # 显示第一帧
        self.show_frame()

    def reload_video(self):
        """重新选择视频并加载"""
        self.load_video()

    def update_mouse_position(self, event):
        """实时更新鼠标坐标"""
        self.mouse_position_label.config(
            text=f"Mouse Position: X={event.x}, Y={event.y}"
        )

    def on_progress_change(self, value):
        """当进度条拖动时，更新当前帧"""
        self.current_frame = int(value)
        self.show_frame()

    def show_frame(self):
        """显示当前帧"""
        if self.frames:
            frame = self.frames[self.current_frame]

            # 将 OpenCV BGR 图像转换为 Pillow 图像
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            # 更新 Tkinter 标签
            self.label.imgtk = imgtk
            self.label.configure(image=imgtk)

            # 更新帧号和时间的显示
            time_in_seconds = self.current_frame / self.fps
            self.frame_label.config(
                text=f"Frame: {self.current_frame} / {self.total_frames}, Time: {time_in_seconds:.2f} sec"
            )

            # 更新进度条
            self.progress.set(self.current_frame)

    def jump_to_frame(self):
        """跳转到指定的帧"""
        try:
            frame_no = int(self.jump_entry.get())
            if 0 <= frame_no < self.total_frames:
                self.current_frame = frame_no
                self.show_frame()
            else:
                messagebox.showerror("Error", "Frame number out of range.")
        except ValueError:
            messagebox.showerror("Error", "Invalid frame number.")

    def select_start_frame(self):
        """选择起始帧坐标"""
        self.selecting_start = True
        self.selecting_end = False
        messagebox.showinfo(
            "Info", "Click on the frame to select the start coordinate."
        )

    def select_end_frame(self):
        """选择结束帧坐标"""
        self.selecting_start = False
        self.selecting_end = True
        messagebox.showinfo("Info", "Click on the frame to select the end coordinate.")

    def get_coordinates(self, event):
        """获取鼠标点击的坐标并显示在界面上"""
        if self.selecting_start:
            self.start_x, self.start_y = event.x, event.y
            self.start_frame = self.current_frame
            self.selecting_start = False
            self.start_coord_label.config(
                text=f"Start Coordinate: (X={self.start_x}, Y={self.start_y}), Frame: {self.start_frame}"
            )
            messagebox.showinfo(
                "Info",
                f"Start coordinate selected: ({self.start_x}, {self.start_y}) at frame {self.start_frame}",
            )
        elif self.selecting_end:
            self.end_x, self.end_y = event.x, event.y
            self.end_frame = self.current_frame
            self.selecting_end = False
            self.end_coord_label.config(
                text=f"End Coordinate: (X={self.end_x}, Y={self.end_y}), Frame: {self.end_frame}"
            )
            messagebox.showinfo(
                "Info",
                f"End coordinate selected: ({self.end_x}, {self.end_y}) at frame {self.end_frame}",
            )

    def apply_blur(self):
        """对指定区域应用高斯模糊"""
        try:
            # 检查是否已经选择了起始和结束帧坐标
            if (
                self.start_x is None
                or self.start_y is None
                or self.end_x is None
                or self.end_y is None
            ):
                raise ValueError("Please select both start and end coordinates.")

            # 计算中间点作为模糊中心
            self.rect_x = (self.start_x + self.end_x) // 2
            self.rect_y = (self.start_y + self.end_y) // 2

            # 获取模糊区域宽度和高度
            self.rect_w = int(self.width_entry.get())
            self.rect_h = int(self.height_entry.get())

            if self.rect_w <= 0 or self.rect_h <= 0:
                raise ValueError("Invalid rectangle dimensions")

            # 处理帧数的范围
            if self.start_frame is None or self.end_frame is None:
                raise ValueError("Start or end frame is not selected.")

            if self.start_frame > self.end_frame:
                raise ValueError("Start frame cannot be greater than end frame")

            self.blurring = True
            print(f"Applying blur from frame {self.start_frame} to {self.end_frame}")

            # 对指定帧范围进行模糊处理
            for i in range(self.start_frame, self.end_frame + 1):
                frame = self.frames[i]

                # 计算矩形区域的边界
                x1 = max(0, self.rect_x - self.rect_w // 2)
                y1 = max(0, self.rect_y - self.rect_h // 2)
                x2 = min(frame.shape[1], self.rect_x + self.rect_w // 2)
                y2 = min(frame.shape[0], self.rect_y + self.rect_h // 2)

                # 对区域进行高斯模糊
                roi = frame[y1:y2, x1:x2]
                blurred_roi = cv2.GaussianBlur(roi, (15, 15), 0)
                frame[y1:y2, x1:x2] = blurred_roi

                self.frames[i] = frame

            # 显示模糊后的帧
            self.show_frame()

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def save_video(self):
        """保存视频"""
        output_file = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
        )
        if not output_file:
            return

        # 获取视频的尺寸
        height, width, layers = self.frames[0].shape
        size = (width, height)

        # 使用 OpenCV 保存视频
        out = cv2.VideoWriter(
            output_file, cv2.VideoWriter_fourcc(*"mp4v"), self.fps, size
        )

        for frame in self.frames:
            out.write(frame)

        out.release()
        messagebox.showinfo("Save Video", f"Video saved as {output_file}")

    def move_left(self, event):
        """按左方向键，移动到上一帧"""
        if self.current_frame > 0:
            self.current_frame -= 1
            self.show_frame()

    def move_right(self, event):
        """按右方向键，移动到下一帧"""
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.show_frame()


# 创建 Tkinter 窗口
root = tk.Tk()

# 创建视频应用程序
app = VideoApp(root)

# 启动 Tkinter 主循环
root.mainloop()
