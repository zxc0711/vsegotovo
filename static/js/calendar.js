<script>
  document.addEventListener('DOMContentLoaded', function () {
    const Calendar = tui.Calendar;

    const calendar = new Calendar('#calendar', {
      defaultView: 'month', // 'week' | 'day'
      useCreationPopup: true,
      useDetailPopup: true,
      calendars: [
        {
          id: '1',
          name: 'Мои события',
          backgroundColor: '#03bd9e',
        }
      ]
    });

    // Пример события
    calendar.createSchedules([
      {
        id: '1',
        calendarId: '1',
        title: 'Пример события',
        category: 'time',
        dueDateClass: '',
        start: '2025-06-01T10:30:00+03:00',
        end: '2025-06-01T12:30:00+03:00'
      }
    ]);
  });
</script>
