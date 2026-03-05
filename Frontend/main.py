# นำเข้าเครื่องมือของ Kivy ที่จำเป็นต้องใช้
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore # [เพิ่ม] นำเข้า JsonStore สำหรับ Save/Load
import sys
import os

# ดึง path ของโฟลเดอร์หลัก เพื่อให้เรียกใช้ Backend ได้
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Backend.sudoku_engine import SudokuEngine

# สร้างคลาสสำหรับกระดาน Sudoku
class SudokuBoard(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 9       
        self.spacing = 2    
        self.padding = 10   
        self.cells = []  
        self.engine = SudokuEngine()

        # ตัวแปรป้องกันการคิดคะแนนตอนสร้างกระดาน
        self.is_generating = False 

        for i in range(81):
            cell = TextInput(
                text='',
                multiline=False,     
                halign='center',     
                font_size=24,
                input_filter='int'   
            )
            
            cell.cell_index = i                   
            cell.bind(text=self.check_answer)     
            
            self.add_widget(cell)
            self.cells.append(cell)

    def check_answer(self, instance, value):
        # ถ้ากำลังสร้างกระดาน หรือลบเป็นช่องว่าง ให้ข้ามไปเลย
        if self.is_generating or value == '':
            return
            
        row = instance.cell_index // 9
        col = instance.cell_index % 9
        num = int(value)

        # ถาม Backend ว่าเลขนี้ถูกไหม?
        is_correct = self.engine.check_move(row, col, num)
        
        app = App.get_running_app()

        if is_correct:
            instance.foreground_color = [0, 0.7, 0, 1]  # สีเขียว
            instance.readonly = True                    # ล็อคช่อง
            app.update_score(100)                       # +100 คะแนน
        else:
            instance.foreground_color = [1, 0, 0, 1]    # สีแดง
            app.update_score(-20)                       # -20 คะแนน

    def clear_board(self, instance=None):
        self.is_generating = True  

        for cell in self.cells:
            cell.text = ''
            cell.readonly = False
            cell.background_color = [1, 1, 1, 1]
            cell.foreground_color = [0, 0, 0, 1]  
            
        self.engine.board = [[0 for _ in range(9)] for _ in range(9)]
        self.is_generating = False 

    def new_game(self, instance=None):
        self.clear_board()
        self.is_generating = True  
        
        board_data = self.engine.generate_board("Easy")
        
        for i in range(81):
            row = i // 9
            col = i % 9
            val = board_data[row][col]
            
            cell = self.cells[i]
            if val != 0:
                cell.text = str(val)
                cell.readonly = True
                cell.background_color = [0.9, 0.9, 0.9, 1] 
                cell.foreground_color = [0, 0, 0, 1] 
            else:
                cell.text = ''
                cell.readonly = False
                cell.background_color = [1, 1, 1, 1]    
                cell.foreground_color = [0, 0, 0, 1] 
                
        self.is_generating = False 


# กำหนดขนาดหน้าต่างแอปเริ่มต้น
Window.size = (500, 700) # เพิ่มความสูงหน้าต่างนิดหน่อยให้พอดีกับปุ่ม 2 แถว

class SudokuApp(App):
    def build(self):
        # สร้างตัวแปร Store ไว้เก็บไฟล์ชื่อ sudoku_save.json
        self.store = JsonStore('sudoku_save.json')

        main_layout = BoxLayout(orientation='vertical')

        self.seconds_elapsed = 0
        self.timer_event = None
        self.score = 0
        
        # --- แถบด้านบน (เวลา & คะแนน) ---
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), padding=10)
        self.timer_label = Label(text="Time: 00:00", font_size=24, color=(1, 1, 1, 1))
        self.score_label = Label(text="Score: 0", font_size=24, color=(1, 1, 0, 1)) 
        top_bar.add_widget(self.timer_label)
        top_bar.add_widget(self.score_label)
        main_layout.add_widget(top_bar)

        # --- กระดาน Sudoku ---
        self.board = SudokuBoard(size_hint=(1, 0.70))
        main_layout.add_widget(self.board)
        
        # --- ปุ่มแถวที่ 1 (ควบคุมเกมหลัก) ---
        row1_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.10), padding=[10, 5, 10, 5], spacing=10)
        btn_new = Button(text="New Game", font_size=20)
        btn_clear = Button(text="Clear", font_size=20)
        btn_hint = Button(text="Hint", font_size=20)
        
        btn_new.bind(on_press=self.start_new_game)
        btn_clear.bind(on_press=self.clear_game)
        btn_hint.bind(on_press=self.give_hint)
        
        row1_layout.add_widget(btn_new)
        row1_layout.add_widget(btn_clear)
        row1_layout.add_widget(btn_hint)
        main_layout.add_widget(row1_layout)

        # --- ปุ่มแถวที่ 2 (Save / Load) ---
        row2_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.10), padding=[10, 5, 10, 10], spacing=10)
        btn_save = Button(text="Save Game", font_size=20, background_color=[0.2, 0.6, 1, 1])
        btn_load = Button(text="Load Game", font_size=20, background_color=[1, 0.6, 0.2, 1])
        
        btn_save.bind(on_press=self.save_game)
        btn_load.bind(on_press=self.load_game)
        
        row2_layout.add_widget(btn_save)
        row2_layout.add_widget(btn_load)
        main_layout.add_widget(row2_layout)

        return main_layout

    def update_timer(self, dt):
        self.seconds_elapsed += 1
        minutes = self.seconds_elapsed // 60
        seconds = self.seconds_elapsed % 60
        self.timer_label.text = f"Time: {minutes:02d}:{seconds:02d}"

    def update_score(self, points):
        self.score += points
        self.score_label.text = f"Score: {self.score}"

    def start_new_game(self, instance):
        self.board.new_game()
        self.seconds_elapsed = 0
        self.timer_label.text = "Time: 00:00"
        self.score = 0
        self.score_label.text = "Score: 0"
        
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def clear_game(self, instance):
        self.board.clear_board() 
        if self.timer_event:
            self.timer_event.cancel()
        self.score = 0
        self.score_label.text = "Score: 0"
        self.seconds_elapsed = 0
        self.timer_label.text = "Time: 00:00"

    def give_hint(self, instance):
        print("💡 กดปุ่ม Hint แล้ว! เตรียมรับคำใบ้...")   

    # --- ฟังก์ชัน Save ---
    def save_game(self, instance):
        cells_data = []
        # เก็บสถานะของช่องแต่ละช่องทั้งหมด
        for cell in self.board.cells:
            cells_data.append({
                'text': cell.text,
                'readonly': cell.readonly,
                'bg_color': cell.background_color,
                'fg_color': cell.foreground_color
            })
        
        # บันทึกลงไฟล์ JsonStore
        self.store.put('saved_level', 
                       time=self.seconds_elapsed,
                       score=self.score,
                       board_engine=self.board.engine.board,
                       solution_engine=self.board.engine.solution,
                       cells=cells_data)
        print("🟢 บันทึกเกมสำเร็จ!")

    # --- ฟังก์ชัน Load ---
    def load_game(self, instance):
        # เช็คก่อนว่ามีไฟล์เซฟอยู่ไหม
        if self.store.exists('saved_level'):
            data = self.store.get('saved_level')
            
            # โหลดเวลา
            self.seconds_elapsed = data['time']
            minutes = self.seconds_elapsed // 60
            seconds = self.seconds_elapsed % 60
            self.timer_label.text = f"Time: {minutes:02d}:{seconds:02d}"
            
            # โหลดคะแนน
            self.score = data['score']
            self.score_label.text = f"Score: {self.score}"
            
            # โหลดกระดานหลังบ้าน (Backend)
            self.board.engine.board = data['board_engine']
            self.board.engine.solution = data['solution_engine']
            
            # โหลดสถานะหน้าจอ (เปิดโหมด is_generating ป้องกันคะแนนเด้งรัวๆ)
            self.board.is_generating = True
            for i, cell_data in enumerate(data['cells']):
                cell = self.board.cells[i]
                cell.text = cell_data['text']
                cell.readonly = cell_data['readonly']
                cell.background_color = cell_data['bg_color']
                cell.foreground_color = cell_data['fg_color']
            self.board.is_generating = False
            
            # ให้เวลาเดินต่อ
            if self.timer_event:
                self.timer_event.cancel()
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)
            
            print("🟠 โหลดเกมสำเร็จ!")
        else:
            print("🔴 ไม่พบไฟล์เซฟเก่า!")

if __name__ == '__main__':
    SudokuApp().run()