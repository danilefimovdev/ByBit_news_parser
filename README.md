<html>
<body>
    <h1>Тестовое задание: Парсер новостей с биржи ByBit</h1>
    <p>Целью было создать парсер, который будет отправлять запросы ежесекундно, и в случае появления новой новости, он должен записывать ее в csv файл. Также, парсер должен обходить возможные блокировки и CDN кэширование.</p>
    <h2>О реализации.</h2>
    <p>Парсер выполнен асинхронно до мозга костей. Он отправляет запрос на api биржи. В функцию main мы передаем параметр from_page_number, который указывает с какой страницы новостей мы начнем проверять наличие свежих новостей (по умолчанию с самой первой). Проверка свежести новости происходит путем сравнения временной метки date_timestamp и title из полученных json данных с json данными самой свежей новости (файл static/last_news.json). Если новость свежее новости в last_news.json, тогда она записывается в csv файл и данные в last_news.json перезаписываются на данные этой новости.</p>
    <p>Парсер проходится по новостям с самой дальней страницы (например, 4) к началу (1) и затем продолжает проверять только первую страницу. Новости проверяются снизу вверх (как они и идут по своей дате публикации). Для каждого запроса формируются новые header данные или изменяются имеющиеся. Какие и сколько header параметров будет в запросе определяется рандомно.</p>
</body>
</html>
