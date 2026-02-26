#this is main.py, the main file of the project. It is responsible for running the app and managing the screens.
# นำเข้าเครื่องมือของ Kivy ที่จำเป็นต้องใช้
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

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

# กำหนดขนาดหน้าต่างแอปเริ่มต้น
Window.size = (500, 650)

# สร้างคลาสหลักของแอปพลิเคชัน
class SudokuApp(App):
    def build(self):
        # Layout หลัก จัดเรียงจากบนลงล่าง (แนวตั้ง)
        main_layout = BoxLayout(orientation='vertical')
        
        # ส่วนที่ 1: นำกระดาน SudokuBoard ที่เราสร้างไว้มาใส่ (ให้พื้นที่ความสูง 85%)
        self.board = SudokuBoard(size_hint=(1, 0.85))
        main_layout.add_widget(self.board)
        
        # ส่วนที่ 2: พื้นที่ปุ่มควบคุมด้านล่าง (ให้พื้นที่ความสูง 15%)
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), padding=10, spacing=10)
        
        btn_clear = Button(text="Clear", font_size=20)
        btn_solve = Button(text="Solve", font_size=20)
        
        button_layout.add_widget(btn_clear)
        button_layout.add_widget(btn_solve)
        
        main_layout.add_widget(button_layout)
        
        return main_layout
    
# คำสั่งสำหรับเริ่มรันโปรแกรม
if __name__ == '__main__':
    SudokuApp().run()