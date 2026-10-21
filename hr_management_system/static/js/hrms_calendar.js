/**
 * HRMS Dashboard Calendar Component
 * Renders an interactive monthly calendar with public holiday highlights,
 * month navigation, today indicator, and monthly holiday list.
 * Supports both Bootstrap 5 and Tailwind CSS dashboard environments.
 */

(function () {
  const MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const DAY_NAMES_SHORT = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
  const DAY_NAMES_FULL = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

  function pad(num) {
    return String(num).padStart(2, "0");
  }

  function formatDateStr(year, month, day) {
    return `${year}-${pad(month + 1)}-${pad(day)}`;
  }

  window.initHRMSDashboardCalendar = function (config) {
    const rootEl = document.getElementById(config.containerId);
    if (!rootEl) return null;

    const theme = config.theme || "bootstrap"; // "bootstrap" or "tailwind"
    const today = new Date();
    let viewYear = config.initialYear || today.getFullYear();
    let viewMonth = (config.initialMonth !== undefined) ? config.initialMonth : today.getMonth();
    let selectedDateStr = null;

    // Holidays store
    let holidayEvents = Array.isArray(config.initialHolidays) ? [...config.initialHolidays] : [];

    // Elements
    const monthLabelEl = rootEl.querySelector(".hrms-cal-month-label");
    const gridEl = rootEl.querySelector(".hrms-cal-grid");
    const holidaysListEl = rootEl.querySelector(".hrms-cal-holidays-list");
    const prevBtn = rootEl.querySelector(".hrms-cal-prev-btn");
    const nextBtn = rootEl.querySelector(".hrms-cal-next-btn");
    const todayBtn = rootEl.querySelector(".hrms-cal-today-btn");
    const holidayCountBadge = rootEl.querySelector(".hrms-cal-holiday-count");

    // Build holiday map for fast lookup: dateStr -> [holiday, ...]
    function getHolidayMap() {
      const map = {};
      holidayEvents.forEach(h => {
        if (!h.date) return;
        const d = (h.date.length > 10) ? h.date.substring(0, 10) : h.date;
        if (!map[d]) map[d] = [];
        // Deduplicate holiday names on the same date
        if (!map[d].some(existing => existing.title === h.title)) {
          map[d].push(h);
        }
      });
      return map;
    }

    function render() {
      const holidayMap = getHolidayMap();

      // 1. Update Month & Year Title
      if (monthLabelEl) {
        monthLabelEl.textContent = `${MONTH_NAMES[viewMonth]} ${viewYear}`;
      }

      // 2. Build Grid Days
      if (gridEl) {
        gridEl.innerHTML = "";

        // First day of month (0 = Sun, 1 = Mon...)
        const firstDayIndex = new Date(viewYear, viewMonth, 1).getDay();
        const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
        const prevMonthLastDay = new Date(viewYear, viewMonth, 0).getDate();

        // Previous month trailing days
        for (let i = firstDayIndex - 1; i >= 0; i--) {
          const dayNum = prevMonthLastDay - i;
          const dayCell = document.createElement("div");
          if (theme === "tailwind") {
            dayCell.className = "h-9 sm:h-10 flex items-center justify-center text-xs font-medium text-purple-300/30 pointer-events-none select-none";
          } else {
            dayCell.className = "hrms-cal-day-cell text-muted opacity-25";
          }
          dayCell.textContent = dayNum;
          gridEl.appendChild(dayCell);
        }

        // Current month days
        for (let day = 1; day <= daysInMonth; day++) {
          const dateStr = formatDateStr(viewYear, viewMonth, day);
          const isToday = (
            day === today.getDate() &&
            viewMonth === today.getMonth() &&
            viewYear === today.getFullYear()
          );

          const holidaysOnDay = holidayMap[dateStr] || [];
          const hasHoliday = holidaysOnDay.length > 0;
          const isPublicHoliday = holidaysOnDay.some(h => (h.category === "PUBLIC" || h.is_public));

          const dayCell = document.createElement("button");
          dayCell.type = "button";
          dayCell.setAttribute("data-date", dateStr);

          // Build class names according to theme
          if (theme === "tailwind") {
            let baseClasses = "h-9 sm:h-10 w-full rounded-xl flex flex-col items-center justify-center text-xs font-bold transition-all relative group cursor-pointer ";
            if (isToday && hasHoliday) {
              dayCell.className = baseClasses + "hrms-cal-today-holiday text-white shadow-lg";
              dayCell.style.background = "linear-gradient(135deg, #7C3AED 0%, #F43F5E 100%)";
              dayCell.style.boxShadow = "0 0 0 2px #F43F5E, 0 0 14px rgba(244, 63, 94, 0.5)";
              dayCell.style.color = "#FFFFFF";
            } else if (isToday) {
              dayCell.className = baseClasses + "hrms-cal-today-day text-white shadow-md";
              dayCell.style.background = "linear-gradient(135deg, #7C3AED 0%, #9333EA 100%)";
              dayCell.style.boxShadow = "0 0 12px rgba(139, 92, 246, 0.55)";
              dayCell.style.color = "#FFFFFF";
            } else if (isPublicHoliday) {
              dayCell.className = baseClasses + "hrms-cal-holiday-day";
              dayCell.style.backgroundColor = "rgba(244, 63, 94, 0.22)";
              dayCell.style.borderColor = "rgba(244, 63, 94, 0.55)";
              dayCell.style.borderWidth = "1px";
              dayCell.style.borderStyle = "solid";
              dayCell.style.color = "#FDA4AF";
            } else if (hasHoliday) {
              dayCell.className = baseClasses + "hrms-cal-holiday-day";
              dayCell.style.backgroundColor = "rgba(245, 158, 11, 0.22)";
              dayCell.style.borderColor = "rgba(245, 158, 11, 0.55)";
              dayCell.style.borderWidth = "1px";
              dayCell.style.borderStyle = "solid";
              dayCell.style.color = "#FCD34D";
            } else {
              dayCell.className = baseClasses + "text-slate-200 hover:bg-purple-900/30 hover:text-white";
              dayCell.style.color = "#F5F3FF";
            }
          } else {
            // Bootstrap theme
            let baseClasses = "hrms-cal-day-cell btn btn-sm p-0 d-flex flex-column align-items-center justify-content-center position-relative ";
            if (isToday && hasHoliday) {
              dayCell.className = baseClasses + "btn-primary text-white fw-bold border border-2 border-danger";
            } else if (isToday) {
              dayCell.className = baseClasses + "btn-primary text-white fw-bold shadow-sm";
            } else if (isPublicHoliday) {
              dayCell.className = baseClasses + "btn-danger-subtle text-danger fw-bold border border-danger-subtle";
            } else if (hasHoliday) {
              dayCell.className = baseClasses + "btn-warning-subtle text-warning-emphasis fw-bold";
            } else {
              dayCell.className = baseClasses + "text-dark btn-light border-0";
            }
          }

          // Inner day number & holiday dot indicator
          const numSpan = document.createElement("span");
          numSpan.textContent = day;
          numSpan.className = "leading-none";
          dayCell.appendChild(numSpan);

          if (hasHoliday) {
            const holidayTitle = holidaysOnDay.map(h => h.title).join(", ");
            dayCell.title = `${holidayTitle} (${isPublicHoliday ? "Public Holiday" : "Holiday"})`;

            const dot = document.createElement("span");
            if (theme === "tailwind") {
              dot.className = "w-1.5 h-1.5 rounded-full mt-0.5";
              if (isToday) {
                dot.style.backgroundColor = "#FFFFFF";
                dot.style.boxShadow = "0 0 4px #FFFFFF";
              } else {
                dot.style.backgroundColor = "#F43F5E";
                dot.style.boxShadow = "0 0 6px #F43F5E";
              }
            } else {
              dot.className = isToday ? "badge-dot bg-white mt-1" : "badge-dot bg-danger mt-1";
            }
            dayCell.appendChild(dot);
          }

          // Click day handler
          dayCell.addEventListener("click", () => {
            selectedDateStr = (selectedDateStr === dateStr) ? null : dateStr;
            renderHolidaysList(holidayMap);
          });

          gridEl.appendChild(dayCell);
        }

        // Next month trailing days to balance 7 columns grid
        const totalCells = firstDayIndex + daysInMonth;
        const remainingCells = (totalCells % 7 === 0) ? 0 : 7 - (totalCells % 7);
        for (let i = 1; i <= remainingCells; i++) {
          const dayCell = document.createElement("div");
          if (theme === "tailwind") {
            dayCell.className = "h-9 sm:h-10 flex items-center justify-center text-xs font-medium text-purple-300/30 pointer-events-none select-none";
          } else {
            dayCell.className = "hrms-cal-day-cell text-muted opacity-25";
          }
          dayCell.textContent = i;
          gridEl.appendChild(dayCell);
        }
      }

      // 3. Render Holidays List for the active month
      renderHolidaysList(holidayMap);
    }

    function renderHolidaysList(holidayMap) {
      if (!holidaysListEl) return;

      const prefix = `${viewYear}-${pad(viewMonth + 1)}`;
      const monthHolidays = [];

      holidayEvents.forEach(h => {
        if (h.date && h.date.startsWith(prefix)) {
          if (!monthHolidays.some(existing => existing.date === h.date && existing.title === h.title)) {
            monthHolidays.push(h);
          }
        }
      });

      monthHolidays.sort((a, b) => a.date.localeCompare(b.date));

      if (holidayCountBadge) {
        holidayCountBadge.textContent = `${monthHolidays.length} ${monthHolidays.length === 1 ? "Holiday" : "Holidays"}`;
      }

      holidaysListEl.innerHTML = "";

      if (monthHolidays.length === 0) {
        const emptyEl = document.createElement("div");
        if (theme === "tailwind") {
          emptyEl.className = "py-4 text-center text-xs font-medium flex flex-col items-center gap-1.5";
          emptyEl.style.color = "#C4B5FD";
          emptyEl.innerHTML = `<i class="bi bi-calendar-x text-base" style="color: #8B81A8;"></i><span>No public holidays in ${MONTH_NAMES[viewMonth]}.</span>`;
        } else {
          emptyEl.className = "text-center text-muted py-3 small";
          emptyEl.innerHTML = `<i class="bi bi-calendar-x d-block mb-1 fs-5 opacity-50"></i>No public holidays in ${MONTH_NAMES[viewMonth]}.`;
        }
        holidaysListEl.appendChild(emptyEl);
        return;
      }

      monthHolidays.forEach(h => {
        const parts = h.date.split("-");
        const dateObj = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
        const dayOfWeek = DAY_NAMES_FULL[dateObj.getDay()] || "";
        const dayNum = parts[2];
        const monthShort = MONTH_NAMES[dateObj.getMonth()].substring(0, 3);
        const isSelected = (selectedDateStr === h.date);

        const itemEl = document.createElement("div");

        if (theme === "tailwind") {
          itemEl.className = "p-3 rounded-xl transition-all border flex items-center justify-between gap-3 hrms-cal-holiday-item";
          itemEl.style.backgroundColor = isSelected ? "rgba(244, 63, 94, 0.2)" : "rgba(244, 63, 94, 0.08)";
          itemEl.style.borderColor = isSelected ? "rgba(244, 63, 94, 0.65)" : "rgba(244, 63, 94, 0.35)";
          itemEl.style.borderLeft = "4px solid #F43F5E";

          itemEl.innerHTML = `
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-10 h-10 rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm"
                   style="background: rgba(244, 63, 94, 0.25); border: 1px solid rgba(244, 63, 94, 0.5);">
                <span class="text-[10px] font-bold uppercase leading-none" style="color: #FDA4AF;">${monthShort}</span>
                <span class="text-sm font-extrabold leading-tight text-white">${dayNum}</span>
              </div>
              <div class="min-w-0">
                <div class="text-xs font-bold text-white truncate" title="${h.title}">${h.title}</div>
                <div class="text-[11px] font-medium flex items-center gap-1.5 mt-0.5" style="color: #C4B5FD;">
                  <span>${dayOfWeek}</span>
                  ${h.description ? `<span style="color: rgba(196, 181, 253, 0.5);">•</span><span class="truncate max-w-[140px]" style="color: rgba(245, 243, 255, 0.7);">${h.description}</span>` : ""}
                </div>
              </div>
            </div>
            <span class="px-2.5 py-1 text-[10px] font-bold rounded-full uppercase tracking-wider shrink-0"
                  style="background: rgba(244, 63, 94, 0.22); color: #FFE4E6; border: 1px solid rgba(244, 63, 94, 0.5); box-shadow: 0 0 8px rgba(244, 63, 94, 0.25);">
              ${h.category === "PUBLIC" || h.is_public !== false ? "Public Holiday" : (h.category || "Holiday")}
            </span>
          `;
        } else {
          // Bootstrap theme
          itemEl.className = `p-2 mb-2 rounded-3 border d-flex align-items-center justify-content-between gap-2 transition-all ${
            isSelected
              ? "bg-danger-subtle border-danger"
              : "bg-light border-light-subtle"
          }`;

          itemEl.innerHTML = `
            <div class="d-flex align-items-center gap-2 min-w-0">
              <div class="bg-white text-danger text-center rounded-2 p-1 px-2 border shadow-sm" style="min-width: 44px;">
                <span class="d-block text-uppercase fw-bold text-danger" style="font-size: 0.65rem; line-height: 1;">${monthShort}</span>
                <span class="d-block fw-bold text-dark fs-6" style="line-height: 1.1;">${dayNum}</span>
              </div>
              <div class="text-truncate">
                <div class="fw-bold text-dark text-truncate" style="font-size: 0.825rem;" title="${h.title}">${h.title}</div>
                <small class="text-muted" style="font-size: 0.725rem;">
                  ${dayOfWeek}${h.description ? ` &bull; ${h.description}` : ""}
                </small>
              </div>
            </div>
            <span class="badge ${h.category === "PUBLIC" || h.is_public !== false ? "bg-danger" : "bg-warning text-dark"} text-uppercase rounded-pill" style="font-size: 0.65rem;">
              ${h.category === "PUBLIC" || h.is_public !== false ? "Public Holiday" : (h.category || "Holiday")}
            </span>
          `;
        }

        holidaysListEl.appendChild(itemEl);
      });
    }

    // Attach event listeners for controls
    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        viewMonth--;
        if (viewMonth < 0) {
          viewMonth = 11;
          viewYear--;
        }
        selectedDateStr = null;
        render();
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        viewMonth++;
        if (viewMonth > 11) {
          viewMonth = 0;
          viewYear++;
        }
        selectedDateStr = null;
        render();
      });
    }

    if (todayBtn) {
      todayBtn.addEventListener("click", () => {
        viewYear = today.getFullYear();
        viewMonth = today.getMonth();
        selectedDateStr = formatDateStr(today.getFullYear(), today.getMonth(), today.getDate());
        render();
      });
    }

    // Initial render
    render();

    // Background fetch from API to ensure fresh events
    const apiUrl = config.apiUrl || "/api/calendar/events/";
    fetch(apiUrl)
      .then(res => res.json())
      .then(data => {
        if (data && data.events && Array.isArray(data.events)) {
          holidayEvents = data.events.filter(e => e.type === "holiday" || e.category === "PUBLIC");
          render();
        }
      })
      .catch(err => {
        console.warn("HRMS Calendar API sync notice:", err);
      });

    return {
      nextMonth: () => { nextBtn && nextBtn.click(); },
      prevMonth: () => { prevBtn && prevBtn.click(); },
      goToToday: () => { todayBtn && todayBtn.click(); },
      setYearMonth: (y, m) => { viewYear = y; viewMonth = m; render(); }
    };
  };
})();

