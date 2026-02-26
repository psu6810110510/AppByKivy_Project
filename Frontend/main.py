#this is main.py, the main file of the project. It is responsible for running the app and managing the screens.
# นำเข้าเครื่องมือของ Kivy ที่จำเป็นต้องใช้
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput

# สร้างคลาสสำหรับกระดาน Sudoku
class SudokuBoard(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 1. ตั้งค่าตาราง: บังคับให้มี 9 คอลัมน์
        self.cols = 9       
        self.spacing = 2    # ระยะห่างระหว่างช่อง
        self.padding = 10   # ระยะขอบรอบกระดาน
        
        # 2. เตรียม List ว่างๆ เอาไว้เก็บช่องตัวเลขทั้ง 81 ช่อง
        self.cells = []     
        
        # 3. วนลูป 81 รอบ เพื่อสร้างช่องกรอกตัวเลข (TextInput)
        for i in range(81):
            cell = TextInput(
                text='',
                multiline=False,     # ไม่ให้กด Enter ขึ้นบรรทัดใหม่
                halign='center',     # จัดตัวเลขให้อยู่ตรงกลาง
                font_size=24,
                input_filter='int'   # ให้กรอกได้เฉพาะตัวเลขเท่านั้น
            )
            # นำช่องที่สร้างเสร็จไปแปะบนกระดาน และเก็บเข้า List
            self.add_widget(cell)
            self.cells.append(cell)