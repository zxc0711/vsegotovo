document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'ru',
        themeSystem: 'bootstrap5',

        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },

        events: '/risks_calendar',
        eventColor: '#378006',

        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        },

        eventDidMount: function(info) {
            // Подсказка с помощью Bootstrap Tooltip с дополнительной инфой о риске
            new bootstrap.Tooltip(info.el, {
                title: `Статус: ${info.event.extendedProps.status}\nМуниципалитет: ${info.event.extendedProps.municipality || 'не указан'}`,
                placement: 'top',
                trigger: 'hover',
                container: 'body'
            });
        },

        eventClick: function(info) {
            // Переход на страницу детали риска вместо alert
            if(info.event.extendedProps.detailUrl) {
                window.location.href = info.event.extendedProps.detailUrl;
            } else {
                alert(`Риск: ${info.event.title}\nСтатус: ${info.event.extendedProps.status}`);
            }
        }
    });

    calendar.render();
});
