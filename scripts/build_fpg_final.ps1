$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$ErrorActionPreference = 'Stop'

$src = 'D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\Грант для гимназии Давыдова\Инженерный грант\index_v3.html'
$dst = 'C:\Users\Admin\.gemini\antigravity\scratch\Мой Дашборд\technostart_fpg_final.html'

$content = Get-Content $src -Raw

$bodyReplacement = @'
<body>
    <div class="slides">
'@
$content = [regex]::Replace(
    $content,
    '(?s)<body>\s*<div class="download-group">.*?</div>\s*<div class="slides">',
    $bodyReplacement,
    1
)

$content = $content.Replace(
    '<span class="slide-num">3</span>' + "`r`n" + '            <h2>Проблема</h2>',
    '<span class="slide-num">2</span>' + "`r`n" + '            <h2>Проблема</h2>'
)
$content = $content.Replace('<span class="slide-num">3б</span>', '<span class="slide-num">3</span>')
$content = $content.Replace(
    '<span class="slide-num" style="top: 24px; right: auto; left: 32px;">4б</span>',
    '<span class="slide-num" style="top: 24px; right: auto; left: 32px;">5</span>'
)
$content = $content.Replace('<span class="slide-num">4в</span>', '<span class="slide-num">6</span>')
$content = $content.Replace(
    '<!-- SLIDE: STAGES OVERVIEW -->' + "`r`n" +
    '        <div class="slide">' + "`r`n" +
    '            <h2 style="margin-bottom:20px;">Дорожная карта проекта</h2>',
    '<!-- SLIDE: STAGES OVERVIEW -->' + "`r`n" +
    '        <div class="slide">' + "`r`n" +
    '            <span class="slide-num">7</span>' + "`r`n" +
    '            <h2 style="margin-bottom:20px;">Дорожная карта проекта</h2>'
)

$content = [regex]::Replace(
    $content,
    '(?s)\s*<!-- SLIDE 6: SCORE OVERVIEW -->.*?<!-- SLIDE 6: WEAK POINTS STRATEGY -->',
    "`r`n`r`n        <!-- SLIDE 8: RESULTS -->",
    1
)

$newSlides = @'
        <!-- SLIDE 8: RESULTS -->
        <div class="slide">
            <span class="slide-num">8</span>
            <h2>Ожидаемые результаты и KPI</h2>
            <p style="margin-bottom:18px;color:var(--muted);">Проект ориентирован не на разовое событие, а на измеримый рост интереса школьников к инженерным направлениям и на создание повторяемой модели профориентации для школ Набережных Челнов.</p>

            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px;margin:22px 0 26px;">
                <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:14px;padding:18px;">
                    <div style="font-size:2rem;font-weight:800;color:#1d4ed8;line-height:1;">200</div>
                    <div style="margin-top:6px;font-weight:600;color:#1e3a8a;">участников 8-10 классов</div>
                    <p style="margin-top:10px;font-size:.92rem;color:#475569;">Не менее 200 школьников пройдут цикл инженерных профессиональных проб на базе Гимназии и школ-партнеров.</p>
                </div>
                <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:14px;padding:18px;">
                    <div style="font-size:2rem;font-weight:800;color:#15803d;line-height:1;">4</div>
                    <div style="margin-top:6px;font-weight:600;color:#166534;">городских фестиваля</div>
                    <p style="margin-top:10px;font-size:.92rem;color:#475569;">Механика, электроника, программирование и прикладные инженерные практики с наставниками из отрасли.</p>
                </div>
                <div style="background:#fff7ed;border:1px solid #fdba74;border-radius:14px;padding:18px;">
                    <div style="font-size:2rem;font-weight:800;color:#c2410c;line-height:1;">+25%</div>
                    <div style="margin-top:6px;font-weight:600;color:#9a3412;">рост интереса к инженерии</div>
                    <p style="margin-top:10px;font-size:.92rem;color:#475569;">Измеряется анкетированием "до/после" по отношению к инженерным профессиям и готовности выбирать технический трек.</p>
                </div>
                <div style="background:#faf5ff;border:1px solid #d8b4fe;border-radius:14px;padding:18px;">
                    <div style="font-size:2rem;font-weight:800;color:#7e22ce;line-height:1;">6+</div>
                    <div style="margin-top:6px;font-weight:600;color:#6b21a8;">партнеров в контуре проекта</div>
                    <p style="margin-top:10px;font-size:.92rem;color:#475569;">Индустриальные, образовательные и школьные партнеры участвуют в фестивалях, наставничестве и тиражировании модели.</p>
                </div>
            </div>

            <div style="display:grid;grid-template-columns:1.15fr .85fr;gap:20px;align-items:start;">
                <div style="background:#f8fafc;border:1px solid var(--border-light);border-radius:14px;padding:18px;">
                    <h3 style="margin-bottom:12px;color:#0f172a;">Количественные и качественные эффекты</h3>
                    <ul style="margin:0;padding-left:18px;line-height:1.6;">
                        <li>не менее 200 участников из 8-10 классов;</li>
                        <li>не менее 4 полноценных фестивалей профессиональных проб;</li>
                        <li>рост информированности о технических образовательных траекториях не менее чем на 30%;</li>
                        <li>формирование базы методических материалов для повторного запуска и тиражирования;</li>
                        <li>появление у школьников подтвержденного созидательного опыта, контакта с инженерами и понимания карьерных маршрутов.</li>
                    </ul>
                </div>
                <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:14px;padding:18px;">
                    <h3 style="margin-bottom:12px;color:#92400e;">Как верифицируется результат</h3>
                    <ul style="margin:0;padding-left:18px;line-height:1.6;">
                        <li>входное и итоговое анкетирование;</li>
                        <li>регистрация участников и листы присутствия;</li>
                        <li>пакет партнерских писем и актов участия;</li>
                        <li>публичные публикации и итоговый отчет проекта;</li>
                        <li>методический пакет для следующего цикла и школ-партнеров.</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- SLIDE 9: RESOURCES -->
        <div class="slide">
            <span class="slide-num">9</span>
            <h2>Ресурсная модель, партнеры и устойчивость</h2>
            <p style="margin-bottom:18px;color:var(--muted);">В презентации фиксируется логика ресурсного обеспечения проекта. Точные суммы и постатейная смета выносятся в бюджетную форму заявки и приложения, чтобы не перегружать слайды и не подменять смету общими тезисами.</p>

            <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;">
                <div style="background:#f8fafc;border:1px solid var(--border-light);border-radius:14px;padding:18px;">
                    <h3 style="margin-bottom:12px;color:#0f172a;">Средства гранта</h3>
                    <ul style="margin:0;padding-left:18px;line-height:1.6;">
                        <li>оборудование и расходные материалы для профпроб;</li>
                        <li>оплата труда методистов, координаторов и профильных наставников;</li>
                        <li>информационное сопровождение и упаковка результатов;</li>
                        <li>организационные расходы, напрямую связанные с календарным планом.</li>
                    </ul>
                </div>
                <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:14px;padding:18px;">
                    <h3 style="margin-bottom:12px;color:#166534;">Собственный вклад и партнеры</h3>
                    <ul style="margin:0;padding-left:18px;line-height:1.6;">
                        <li>помещения, инфраструктура и кадровый ресурс Гимназии;</li>
                        <li>вклад школ-партнеров в набор и сопровождение участников;</li>
                        <li>индустриальное участие ПАО "КАМАЗ" и профильных экспертов;</li>
                        <li>партнерский контур СПО/вузов для демонстрации образовательных маршрутов.</li>
                    </ul>
                </div>
                <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:14px;padding:18px;">
                    <h3 style="margin-bottom:12px;color:#1d4ed8;">Устойчивость после гранта</h3>
                    <ul style="margin:0;padding-left:18px;line-height:1.6;">
                        <li>повторяемый формат фестивалей и готовый сценарный пакет;</li>
                        <li>открытые методические материалы и публичный отчет;</li>
                        <li>встраивание практик в профориентационную работу Гимназии;</li>
                        <li>масштабирование модели на школы Набережных Челнов и Республики Татарстан.</li>
                    </ul>
                </div>
            </div>

            <div style="margin-top:22px;background:#fff7ed;border:1px solid #fdba74;border-radius:14px;padding:18px;">
                <strong style="display:block;margin-bottom:8px;color:#9a3412;">Информационная открытость проекта</strong>
                <p style="margin:0;color:#7c2d12;line-height:1.6;">Ход реализации и результаты проекта публикуются на ресурсах Гимназии, в городских медиа и партнерских каналах. Публичная отчетность усиливает доверие к проекту, подтверждает социальный эффект и поддерживает следующий цикл набора участников.</p>
            </div>
        </div>

        <!-- APPENDIX 1: SURVEY INFOGRAPHICS -->
'@
$content = [regex]::Replace(
    $content,
    '(?s)<!-- SLIDE 8: RESULTS -->.*?<!-- APPENDIX 1: SURVEY INFOGRAPHICS -->',
    $newSlides,
    1
)

$content = $content.Replace(
    'Приложение 2 &mdash; Инфографика результатов опроса',
    'Приложение 3 &mdash; Инфографика результатов опроса'
)

Set-Content -Path $dst -Value $content -Encoding UTF8
Write-Output "STAGED=$dst"
