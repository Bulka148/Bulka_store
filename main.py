from flask import Flask, render_template, request, redirect, session, flash
from dbutils import Database


app = Flask(__name__)
app.secret_key = '123'
db = Database()

#Переход на главную страницу
@app.route("/", methods=['POST', 'GET'])
def index():
    my_filter = {'min_price': int(request.form['min_price']) if request.form.get('min_price') else 0,
                 'max_price': int(request.form['max_price']) if request.form.get('max_price') else 0,
                 'bread_type': ''}

    human = session['human'] if 'human' in session else {'id': 0, 'login': 'Неизвестный', 'email': '', 'is_admin': False}
    print(6)
    return render_template("index.html", bread=db.get_bread(), human=human, filter=my_filter,
                           cart=db.get_from_cart(human['id']), favourite=db.get_from_favourite(human['id']))

#Та же главная страница, но при условии выбора категории продукта
@app.route("/type_bread/<string:b_type>", methods=['POST', 'GET'])
def type_bread(b_type):
    my_filter = {'min_price': int(request.form['min_price']) if request.form.get('min_price') else 0,
                 'max_price': int(request.form['max_price']) if request.form.get('max_price') else 0,
                 'bread_type': b_type}

    human = session['human'] if 'human' in session else {'id': 0, 'login': 'Неизвестный', 'email': '',
                                                         'is_admin': False}
    return render_template("index.html", bread=db.get_bread(), human=human, filter=my_filter,
                           cart=db.get_from_cart(human['id']), favourite=db.get_from_favourite(human['id']))

#Корзина (с высчитыванием общей стоимости)
@app.route("/cart")
def cart():
    bread_ids = db.get_from_cart(session['human']['id'])
    human_bread = [p for p in db.get_bread() if p['id'] in bread_ids] #создание переменной сущностей продуктов
    full_price = sum([p['price'] for p in human_bread])
    return render_template("cart.html", human_bread=human_bread, human=session['human'], full_price=full_price)

#Удаление из корзины (не является новой страницей)
@app.route("/delete_from_cart/<int:bread_id>")
def delete_from_cart(bread_id):
    db.delete_from_cart(session['human']['id'], bread_id)
    return redirect('/cart')

#Избранное (тот же аналог корзины, без общей цены)
@app.route("/favourite")
def favourite():
    bread_ids = db.get_from_favourite(session['human']['id'])
    human_bread = [p for p in db.get_bread() if p['id'] in bread_ids]
    return render_template("favourite.html", human_bread=human_bread, human=session['human'])

#Удаление из избранных (тоже не является новой страницей)
@app.route("/delete_from_favourite/<int:bread_id>")
def delete_from_favourite(bread_id):
    db.delete_from_favourite(session['human']['id'], bread_id)
    return redirect('/favourite')

#Авторизация (сначала get для проверки корректности данных, после же в случае успеха post)
@app.route("/authorization", methods=['POST', 'GET'])
def authorization():
    if request.method == 'POST':
        human = db.get_human(request.form['login'], request.form['password'])
        if human:
            session['human'] = human #добавление пользователя в сессию
        return redirect("/")
    elif request.args:
        if not request.args['password']:
            return {'status': 'error', 'message': 'Ведите пароль'}

        human = db.get_human(request.args['login'], request.args['password'])
        return {'status': 'ok'} if human else {'status': 'error', 'message': 'Пользователь не найден'}
    return render_template("authorization.html")

#Регистрация работает аналогично авторизации (если всё ок, то добавляем в базу, иначе же ошибки регистрации выводит)
@app.route("/registration", methods=['POST', 'GET'])
def registration():
    if request.method == 'POST':
        human = {'login': request.form.get('login'),
                 'password': request.form.get('password')}
        human['id'] = db.add_human(human) #добавление пользователя в БД
        session['human'] = human #а теперь добавление в сессию
        return redirect("/")
    elif request.args:
        if not request.args['login']:
            return {'status': 'error', 'message': 'Введи свой ник'}
        if db.get_human(request.args['login'], ''):
            return {'status': 'error', 'message': 'Пользователь с таким логином уже существует'}
        if len(request.args['password']) < 6:
            return {'status': 'error', 'message': 'Пароль слишком короткий'}
        if request.args['password'] != request.args['password2']:
            return {'status': 'error', 'message': 'Пароли не совпадают'}
        return {'status': 'ok'}
    return render_template("registration.html")

#Профиль
@app.route("/profile", methods=['POST', 'GET'])
def profile():
    if request.method == 'POST':
        human = {'id': session['human']['id'],
                 'login': request.form.get('login'),
                 'password': request.form.get('password')}
        db.edit_human(session['human']['id'], human)
        session['human'] = human
        flash('Профиль изменен')
        return redirect("/")

    #Получаем заказы в своём профиле (мы берём все айдишки заказов пользователя, после чего получаем все товары заказов)
    bookings = [db.get_booking(booking_id) for booking_id in db.get_bookings_id(session['human']['id'])]
    return render_template("profile.html", human=session.get('human'), bookings=bookings)

#Добавление товара для админа (add_bread только для админов)
@app.route("/add_bread", methods=['POST', 'GET'])
def add_bread():
    if request.method == 'POST':
        bread = {'name': request.form.get('name'),
                 'price': request.form.get('price'),
                 'type': request.form.get('type')}
        bread_id = db.add_bread(bread)
        request.files.get('photo').save(f'static/bread{bread_id}.jpg')

        flash('Товар добавлен')
        return redirect('/')

    return render_template("add_bread.html")

#Изменение товара
@app.route("/edit_bread/<int:bread_id>", methods=['POST', 'GET'])
def edit_bread(bread_id):
    if request.method == 'POST':
        bread = {'id': bread_id,
                 'name': request.form.get('name'),
                 'price': request.form.get('price'),
                 'type': request.form.get('type')}
        db.edit_bread(bread_id, bread)
        # чтобы фото в случае его неизменения не удалялось
        if request.files['photo']:
            request.files.get('photo').save(f'static/bread{bread_id}.jpg')

        flash('Товар успешно изменен')
        return redirect('/')

    return render_template("edit_bread.html", bread=db.get_bread(bread_id=bread_id))

#Удаление товара
@app.route("/delete_bread/<int:bread_id>")
def delete_bread(bread_id):
    db.delete_bread(bread_id)
    flash('Товар удален')
    return redirect('/')

#Добавление товара в корзину
@app.route("/add_to_cart")
def add_to_cart():
    if 'human' not in session:
        return {'status': 'warning', 'message': 'Необходимо авторизоваться, чтобы купить этот товар'}
    if int(request.args['bread_id']) in db.get_from_cart(session['human']['id']):
        return {'status': 'warning', 'message': 'Этот товар уже в корзине'}

    db.add_to_cart(session['human']['id'], request.args['bread_id'])
    return {'status': 'success', 'message': 'Добавлено в корзину'}

#Добавление товара в избранное
@app.route("/add_to_favourite")
def add_to_favourite():
    if 'human' not in session:
        return {'status': 'warning', 'message': 'Необходимо авторизоваться, чтобы добавить в Избранное этот товар'}
    if int(request.args['bread_id']) in db.get_from_favourite(session['human']['id']):
        return {'status': 'warning', 'message': 'Этот товар уже в Избранном'}

    db.add_to_favourite(session['human']['id'], request.args['bread_id'])
    return {'status': 'success', 'message': 'Добавлено в Избранное'}

#Сделать заказ
@app.route("/make_booking")
def make_booking():
    bread_ids = db.get_from_cart(session['human']['id'])
    db.make_booking(session['human']['id'], bread_ids)
    for bread_id in bread_ids:
        db.delete_from_cart(session['human']['id'], bread_id)
    flash('Заказ принят')
    return redirect('/')

#Страница заказов
@app.route("/booking/<int:booking_id>")
def booking(booking_id):
    booking_data = db.get_booking(booking_id)
    return render_template("booking.html", human=session['human'], booking=booking_data)


# @app.errorhandler(Exception)
# def handle_exception(error):
#     return render_template("error.html", error=error)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
