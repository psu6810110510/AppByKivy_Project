# นำเข้าเครื่องมือของ Kivy ที่จำเป็นต้องใช้
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore 
from kivy.uix.popup import Popup
import sys
import os

# แก้ไข Path สำหรับดึง Backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Backend.sudoku_engine import SudokuEngine

class SudokuBoard(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 9       
        self.spacing = 2    
        self.padding = 10   
        self.cells = []  
        self.engine = SudokuEngine()
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
            cell.last_text = ''           
            cell.bind(text=self.check_answer)     
            
            self.add_widget(cell)
            self.cells.append(cell)

    def check_answer(self, instance, value):
        if self.is_generating:
            return
            
        # 1. Input Validation
        if value != '':
            if len(value) > 1 or value not in "123456789":
                self.is_generating = True
                instance.text = instance.last_text
                self.is_generating = False
                return

        app = App.get_running_app()

        # 2. กรณีผู้เล่นลบเลข
        if value == '':
            app.record_history(
                index=instance.cell_index,
                old_text=instance.last_text, new_text='',
                old_color=instance.foreground_color[:], new_color=[0, 0, 0, 1],
                old_readonly=instance.readonly, new_readonly=False,
                score_diff=0
            )
            self.is_generating = True
            instance.foreground_color = [0, 0, 0, 1]
            instance.last_text = ''
            self.is_generating = False
            return

        # 3. ตรวจคำตอบ
        row = instance.cell_index // 9
        col = instance.cell_index % 9
        num = int(value)

        is_correct = self.engine.check_move(row, col, num)
        
        old_color = instance.foreground_color[:]
        old_readonly = instance.readonly

        if is_correct:
            new_color = [0, 0.7, 0, 1]
            new_readonly = True
            score_diff = 100
        else:
            new_color = [1, 0, 0, 1]
            new_readonly = False 
            score_diff = -20

        app.record_history(
            index=instance.cell_index,
            old_text=instance.last_text, new_text=value,
            old_color=old_color, new_color=new_color,
            old_readonly=old_readonly, new_readonly=new_readonly,
            score_diff=score_diff
        )

        self.is_generating = True
        instance.foreground_color = new_color
        instance.readonly = new_readonly
        instance.last_text = value
        self.is_generating = False
        app.update_score(score_diff)

        # [แก้ไขเพิ่ม] ถ้าตอบถูก ให้เช็คว่าชนะเกมหรือยัง
        if is_correct:
            Clock.schedule_once(lambda dt: self.check_win(), 0.1)

    def clear_board(self, instance=None):
        self.is_generating = True  
        for cell in self.cells:
            cell.text = ''
            cell.last_text = ''
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
                cell.last_text = str(val)
                cell.readonly = True
                cell.background_color = [0.9, 0.9, 0.9, 1] 
                cell.foreground_color = [0, 0, 0, 1] 
            else:
                cell.text = ''
                cell.last_text = ''
                cell.readonly = False
                cell.background_color = [1, 1, 1, 1]    
                cell.foreground_color = [0, 0, 0, 1] 
        self.is_generating = False
    
    def get_hint_data(self):
        for i, cell in enumerate(self.cells):
            if cell.readonly:
                continue
            row = i // 9
            col = i % 9
            correct_val = self.engine.solution[row][col]
            if cell.text == '' or cell.text != str(correct_val):
                return i, correct_val
        return None, None
    
    def check_win(self):
        for cell in self.cells:
            if not cell.readonly: # ถ้ามีช่องไหนยังไม่ล็อค (แปลว่ายังไม่ถูก) = ยังไม่ชนะ
                return False
        self.show_win_popup()
        return True

    def show_win_popup(self):
        app = App.get_running_app()
        if app.timer_event:
            app.timer_event.cancel()

        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        win_label = Label(
            text=f"🎉 ยินดีด้วย คุณชนะแล้ว! 🎉\n\n{app.timer_label.text}\nScore: {app.score}", 
            font_size=20, halign='center'
        )
        btn_play_again = Button(text="Play Again", size_hint=(1, 0.4), font_size=20)
        
        content.add_widget(win_label)
        content.add_widget(btn_play_again)

        popup = Popup(title='Game Clear!', content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        
        def restart_game(instance):
            popup.dismiss()
            app.start_new_game(None)
            
        btn_play_again.bind(on_press=restart_game)
        popup.open()


Window.size = (500, 700) 

class SudokuApp(App):
    def build(self):
        self.store = JsonStore('sudoku_save.json')
        self.undo_stack = []
        self.redo_stack = []

        main_layout = BoxLayout(orientation='vertical')
        self.seconds_elapsed = 0
        self.timer_event = None
        self.score = 0
        
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), padding=10)
        self.timer_label = Label(text="Time: 00:00", font_size=24, color=(1, 1, 1, 1))
        self.score_label = Label(text="Score: 0", font_size=24, color=(1, 1, 0, 1)) 
        top_bar.add_widget(self.timer_label)
        top_bar.add_widget(self.score_label)
        main_layout.add_widget(top_bar)

        self.board = SudokuBoard(size_hint=(1, 0.60))
        main_layout.add_widget(self.board)
        
        # ปุ่มแถว 1
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

        # ปุ่มแถว 2
        row2_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.10), padding=[10, 5, 10, 5], spacing=10)
        btn_undo = Button(text="Undo", font_size=20, background_color=[0.8, 0.8, 0.8, 1], color=[0,0,0,1])
        btn_redo = Button(text="Redo", font_size=20, background_color=[0.8, 0.8, 0.8, 1], color=[0,0,0,1])
        btn_undo.bind(on_press=self.undo_move)
        btn_redo.bind(on_press=self.redo_move)
        row2_layout.add_widget(btn_undo)
        row2_layout.add_widget(btn_redo)
        main_layout.add_widget(row2_layout)

        # ปุ่มแถว 3
        row3_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.10), padding=[10, 5, 10, 10], spacing=10)
        btn_save = Button(text="Save Game", font_size=20, background_color=[0.2, 0.6, 1, 1])
        btn_load = Button(text="Load Game", font_size=20, background_color=[1, 0.6, 0.2, 1])
        btn_save.bind(on_press=self.save_game)
        btn_load.bind(on_press=self.load_game)
        row3_layout.add_widget(btn_save)
        row3_layout.add_widget(btn_load)
        main_layout.add_widget(row3_layout)

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
        self.undo_stack.clear()
        self.redo_stack.clear()
        
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
        self.undo_stack.clear()
        self.redo_stack.clear()

    def record_history(self, index, old_text, new_text, old_color, new_color, old_readonly, new_readonly, score_diff):
        action = {
            'index': index, 'old_text': old_text, 'new_text': new_text,
            'old_color': old_color, 'new_color': new_color,
            'old_readonly': old_readonly, 'new_readonly': new_readonly,
            'score_diff': score_diff
        }
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def undo_move(self, instance):
        if not self.undo_stack:
            return
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        cell = self.board.cells[action['index']]
        self.board.is_generating = True
        cell.text = action['old_text']
        cell.last_text = action['old_text']
        cell.foreground_color = action['old_color']
        cell.readonly = action['old_readonly']
        self.board.is_generating = False
        self.update_score(-action['score_diff'])

    def redo_move(self, instance):
        if not self.redo_stack:
            return
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        cell = self.board.cells[action['index']]
        self.board.is_generating = True
        cell.text = action['new_text']
        cell.last_text = action['new_text']
        cell.foreground_color = action['new_color']
        cell.readonly = action['new_readonly']
        self.board.is_generating = False
        self.update_score(action['score_diff'])

    def save_game(self, instance):
        cells_data = []
        for cell in self.board.cells:
            cells_data.append({
                'text': cell.text, 'readonly': cell.readonly,
                'bg_color': cell.background_color, 'fg_color': cell.foreground_color,
                'last_text': cell.last_text
            })
        self.store.put('saved_level', 
                       time=self.seconds_elapsed, score=self.score,
                       board_engine=self.board.engine.board,
                       solution_engine=self.board.engine.solution,
                       cells=cells_data)

    def load_game(self, instance):
        if self.store.exists('saved_level'):
            data = self.store.get('saved_level')
            self.seconds_elapsed = data['time']
            self.score = data['score']
            self.score_label.text = f"Score: {self.score}"
            self.board.engine.board = data['board_engine']
            self.board.engine.solution = data['solution_engine']
            
            self.board.is_generating = True
            for i, cell_data in enumerate(data['cells']):
                cell = self.board.cells[i]
                cell.text = cell_data['text']
                cell.last_text = cell_data.get('last_text', '')
                cell.readonly = cell_data['readonly']
                cell.background_color = cell_data['bg_color']
                cell.foreground_color = cell_data['fg_color']
            self.board.is_generating = False
            self.undo_stack.clear()
            self.redo_stack.clear()

    def give_hint(self, instance):
        cell_index, correct_val = self.board.get_hint_data()
        if cell_index is not None:
            cell = self.board.cells[cell_index]
            old_color = cell.foreground_color[:]
            old_readonly = cell.readonly
            
            self.record_history(
                index=cell_index,
                old_text=cell.last_text, new_text=str(correct_val),
                old_color=old_color, new_color=[0, 0.4, 1, 1],
                old_readonly=old_readonly, new_readonly=True,
                score_diff=-30
            )

            self.board.is_generating = True
            cell.text = str(correct_val)
            cell.last_text = str(correct_val)
            cell.foreground_color = [0, 0.4, 1, 1] 
            cell.readonly = True
            self.board.is_generating = False
            self.update_score(-30)

            # [แก้ไขเพิ่ม] หลังให้ Hint ให้เช็คด้วยว่าชนะหรือยัง
            Clock.schedule_once(lambda dt: self.board.check_win(), 0.1)

if __name__ == '__main__':
    SudokuApp().run()