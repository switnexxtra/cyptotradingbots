# blueprints/main/routes.py
from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    Company_name="YourCompanyName"
    return render_template('main/index.html', Company_name=Company_name)

@main.route('/about')
def about():
    return render_template('main/about-us.html')


@main.route('/services')
def services():
    return render_template('main/service.html')

@main.route('/blog')
def blog():
    return render_template('main/blog.html')

@main.route('/contact')
def contact():
    return render_template('main/contact.html')

@main.route('/elements')
def elements():
    return render_template('main/elements.html')


@main.route('/feature')
def feature():
    return render_template('main/feature.html')


@main.route('/offer')
def offer():
    return render_template('main/offer.html')


@main.route('/team')
def team():
    return render_template('main/team.html')

@main.route('/testimonial')
def testimonial():
    return render_template('main/testimonial.html')


@main.route('/FAQ')
def FAQ():
    return render_template('main/FAQ.html')

@main.route('/404')
def page_not_found():
    return render_template('main/404.html')


