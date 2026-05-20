function goTop() { $('html, body').animate({ scrollTop: 0 }, 300); }
$(window).scroll(function() {
    if ($(this).scrollTop() > 300) { $('#goTopBtn').fadeIn(); } else { $('#goTopBtn').fadeOut(); }
});
$(document).on('click', 'a[href^="#"]', function(event) {
    event.preventDefault();
    var target = $(this.getAttribute('href'));
    if (target.length) {
        $('html, body').stop().animate({ scrollTop: target.offset().top - 70 }, 500);
    }
});
