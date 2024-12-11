import random
from flask import Flask, render_template, redirect, url_for, request, session
import csv

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # セッションを使うためのキー

# CSVファイルを読み込む関数
def read_csv():
    filename = 'words.csv'  # 固定のCSVファイル名
    words = []
    try:
        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                words.append(row)
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return []  # 空のリストを返す
    return words

# フロントページ
@app.route('/')
def index():
    return render_template('index.html')

# 各kappaleの問題選択ページ
@app.route('/quiz/<language>')
def quiz_select(language):
    words = read_csv()
    kappale_numbers = sorted(set([word['kappale'] for word in words]))  # 章の番号を抽出
    return render_template('kappale_selection.html', kappale_numbers=kappale_numbers, language=language)

# 問題ページ
@app.route('/quiz/<language>/kappale_<int:kappale_num>/start')
def start_quiz(language, kappale_num):
    words = read_csv()
    chapter_words = [word for word in words if int(word['kappale']) == kappale_num]
    
    if len(chapter_words) < 15:
        return f"Error: Not enough questions in chapter {kappale_num}."

    quiz_questions = random.sample(chapter_words, min(len(chapter_words), 15))

    # クイズデータをセッションに保存
    session['quiz_data'] = quiz_questions
    session['current_question'] = 0
    session['score'] = 0
    session['language'] = language
    session['kappale_num'] = kappale_num
    session['incorrect_answers'] = []  # 間違えた問題を格納するリスト

    return redirect(url_for('quiz_question'))

@app.route('/quiz/question', methods=['GET', 'POST'])
def quiz_question():
    if 'quiz_data' not in session or 'current_question' not in session:
        return redirect(url_for('index'))

    quiz_data = session['quiz_data']
    current_question = session['current_question']
    language = session['language']

    # 現在の質問が範囲外の場合は結果ページへ
    if current_question >= len(quiz_data):
        return redirect(url_for('quiz_result'))

    if request.method == 'POST':
        # 正解を判定
        selected_answer = request.form.get('answer')
        correct_answer = quiz_data[current_question]['Finnish'] if language == 'en_fi' else quiz_data[current_question]['English']

        # 正解チェック
        if selected_answer == correct_answer:
            session['score'] += 1
            feedback = "Correct!"
            correct_answer_display = ""  # 正解の場合は表示しない
        else:
            feedback = "Wrong!"
            correct_answer_display = f"Correct Answer: {correct_answer}"  # 間違えた場合の正解を表示
            # 間違えた問題を記録
            session['incorrect_answers'].append({
                'question': quiz_data[current_question]['English'] if language == 'en_fi' else quiz_data[current_question]['Finnish'],
                'correct_answer': correct_answer
            })

        # 次の問題に進む準備
        session['current_question'] += 1
        return render_template('feedback.html', feedback=feedback, correct_answer=correct_answer_display, is_last=session['current_question'] >= len(quiz_data))

    # 現在の問題を表示
    question_data = quiz_data[current_question]
    question_text = question_data['English'] if language == 'en_fi' else question_data['Finnish']
    correct_answer = question_data['Finnish'] if language == 'en_fi' else question_data['English']

    # 選択肢を作成
    if language == 'en_fi':
        wrong_answers = random.sample(
            [w['Finnish'] for w in quiz_data if w['English'] != question_data['English']], 
            min(3, len(quiz_data) - 1)  # 無駄なエラーを防止
        )
    else:
        wrong_answers = random.sample(
            [w['English'] for w in quiz_data if w['Finnish'] != question_data['Finnish']], 
            min(3, len(quiz_data) - 1)
        )

    # 正解を含む選択肢をランダムに並べる
    choices = random.sample([correct_answer] + wrong_answers, len(wrong_answers) + 1)

    return render_template('question.html', question=question_text, choices=choices)

@app.route('/quiz/result')
def quiz_result():
    if 'score' not in session or 'quiz_data' not in session:
        return redirect(url_for('index'))

    score = session['score']
    total_questions = len(session['quiz_data'])
    incorrect_answers = session['incorrect_answers']

    # スコアメッセージ
    if score == total_questions:
        message = f"{score}/{total_questions}! You are perfect! / Olet Täydellinen!"
    elif score >= total_questions * 0.9:
        message = f"{score}/{total_questions}! Nicely Done!"
    elif score >= total_questions * 0.8:
        message = f"{score}/{total_questions}! Keep it up!"
    else:
        message = f"Your score is {score}/{total_questions}!"

    # セッションをクリア
    session.clear()

    return render_template('result.html', score=score, message=message, incorrect_answers=incorrect_answers)

if __name__ == "__main__":
    app.run(debug=True)
