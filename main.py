from app import app

@app.route('/')
def home():
    from flask import session, render_template, redirect, url_for
    print(app.jinja_loader.searchpath)

    if 'username' in session:
        return render_template('index.html')
    return redirect(url_for('login'))


from flask import render_template

@app.route("/faq")
def faq():
    return render_template("faq.html")


if __name__ == '__main__':
    app.run(debug=True)
