
(() => {
const K = {
  // Math helpers
  TAU: Math.PI * 2, // полный оборот, рад
  DEG_TO_RAD: Math.PI / 180, // градусы -> радианы
  RAD_TO_DEG: 180 / Math.PI, // радианы -> градусы
  HALF: 0.5, // коэффициент 1/2
  TWO: 2, // коэффициент 2

  // Input defaults and clamps
  SPEED_MIN: 0.2, // минимальная скорость, м/с
  SPEED_DEFAULT: 11, // скорость по умолчанию, м/с
  ANGLE_DEFAULT_DEG: 35, // угол по умолчанию, градусы
  ANGLE_MIN_DEG: 1, // минимальный угол, градусы
  ANGLE_MAX_DEG: 89, // максимальный угол, градусы
  ANGLE_LABEL_FALLBACK: 0, // fallback угла в подписи
  SPIN_DEFAULT_RPS: 120, // spin по умолчанию, об/с
  FRICTION_MUL_MIN: 0.2, // минимум глобального множителя трения
  FRICTION_MUL_MAX: 1.5, // максимум глобального множителя трения
  FRICTION_MUL_DIGITS: 2, // знаков после запятой для отображения множителя
  VIEW_SCALE_DEFAULT: 1, // масштаб по умолчанию
  BALL_RADIUS_DEFAULT_MM: 20, // радиус по умолчанию, мм
  BALL_RADIUS_MIN_MM: 10, // минимум радиуса, мм
  BALL_RADIUS_MAX_MM: 30, // максимум радиуса, мм
  MM_TO_M: 0.001, // перевод мм -> м
  BALL_MASS_HOLLOW: 0.0027, // масса полого мяча, кг
  BALL_MASS_SOLID: 0.014, // масса сплошного мяча, кг
  BALL_INERTIA_HOLLOW: 0.67, // фактор момента инерции полого мяча
  BALL_INERTIA_SOLID: 0.4, // фактор момента инерции сплошного мяча
  BALL_K_MIN: 1000, // минимальная жесткость мяча
  BALL_K_DEFAULT: 62000, // жесткость мяча по умолчанию
  BALL_C_MIN: 0, // минимальное демпфирование мяча
  BALL_C_DEFAULT: 10.5, // демпфирование мяча по умолчанию

  // Validation
  LAYERS_MIN_COUNT: 1, // минимальное количество слоев
  LAYER_MIN_THICKNESS: 0, // минимальная толщина слоя, мм
  LAYER_MIN_STIFFNESS: 0, // минимальная жесткость слоя
  LAYER_MIN_DAMPING: 0, // минимальное демпфирование слоя
  LAYER_MIN_MU: 0, // минимальный коэффициент трения
  PARSE_INT_BASE: 10, // основание для parseInt
  LAYER_STEP_T: 0.1, // шаг изменения толщины слоя
  LAYER_STEP_KN: 1000, // шаг изменения нормальной жесткости
  LAYER_STEP_CN: 1, // шаг изменения нормального демпфирования
  LAYER_STEP_KT: 1000, // шаг изменения тангенциальной жесткости
  LAYER_STEP_CT: 1, // шаг изменения тангенциального демпфирования
  LAYER_STEP_MU: 0.01, // шаг изменения коэффициентов трения
  LAYER_STEP_PK: 5, // шаг изменения жесткости шипов
  LAYER_STEP_PH: 0.1, // шаг изменения высоты шипов

  // Simulation - time and mesh
  SIM_DT_HIGH: 1.2e-5, // шаг времени (high)
  SIM_DT_NORMAL: 2e-5, // шаг времени (normal)
  SIM_FRAME_DT_HIGH: 8e-5, // шаг сохранения кадров (high)
  SIM_FRAME_DT_NORMAL: 1.1e-4, // шаг сохранения кадров (normal)
  SIM_MAX_T: 0.024, // максимальная длительность контакта, с
  SIM_N_HIGH: 241, // число узлов по X (high)
  SIM_N_NORMAL: 161, // число узлов по X (normal)
  SIM_HALF_WIDTH: 0.08, // половина ширины моделируемой поверхности, м
  SIM_MIN_VY_IN: 0.1, // минимальная входная нормальная скорость, м/с
  GRAVITY: 9.81, // ускорение свободного падения, м/с^2
  PRECONTACT_PX: 180, // длина подлета до удара в пикселях (при масштабе 1)
  PRECONTACT_TIME_MAX: 0.004, // максимум времени подлета, с (ограничение по скорости)
  SIM_UX_LIM_FACTOR: 0.42, // ограничение горизонтального смещения
  SIM_UX_LIM_MIN: 2e-4, // минимальный предел для ux
  SIM_UY_LIM: 0.006, // предел вертикального смещения узлов, м
  SIM_FN_CAP_MIN: 120, // минимальный кап Fn
  SIM_FN_CAP_VY_BIAS: 6, // добавка скорости для расчета капа Fn
  SIM_FN_CAP_FACTOR: 0.11, // масштаб капа Fn
  SIM_KE_CAP_FACTOR: 0.999, // кап энергии на контакте
  SIM_CONTACT_RADIUS_EXTRA: 3, // запас по радиусу контакта (в узлах)
  SIM_CONTACT_R_MARGIN: 1.02, // доп. запас по радиусу контакта
  SIM_HERTZ_EXP: 1.35, // показатель в контактном законе
  SIM_STICK_DECAY: 0.985, // релаксация накопленного stick
  SIM_TILT_MS_GAIN: 0.14, // усиление mu_s от наклона шипов
  SIM_TILT_MK_GAIN: 0.08, // усиление mu_k от наклона шипов
  SIM_TILT_OUT_SCALE: 0.65, // масштаб наклона для шипов внутрь
  SIM_TILT_FORCE_GAIN: 0.12, // усиление касательной силы от наклона
  SIM_PRESSURE_EPS: 1e-8, // epsilon для давления
  SIM_PRESSURE_DX_SCALE: 0.012, // масштаб площади контакта по dx
  SIM_NO_CONTACT_BREAK: 8, // число шагов без контакта до отрыва
  SIM_DETACH_Y_MARGIN: 0.0015, // зазор Y для отрыва
  SIM_DETACH_VY_THRESHOLD: -0.01, // порог vy для отрыва
  SIM_THETA_CLAMP: 0.7, // ограничение наклона шипов
  SIM_THETA_DAMP: 0.95, // демпфирование наклона шипов
  SIM_NODE_V_CLAMP: 6, // предел скорости узлов
  SIM_UY_MAX: 0.0015, // верхний предел вертикального смещения
  SIM_POST_DUR: 0.06, // длительность пост-полета, с
  SIM_SPIN_AIR_DAMP: 0.06, // затухание spin в полете
  SIM_ENERGY_EPS: 1e-12, // epsilon для энергии
  SIM_SLIP_TIME_EPS: 1e-9, // epsilon для деления по времени
  M_TO_MM: 1000, // перевод м -> мм
  S_TO_MS: 1000, // перевод секунд -> миллисекунды
  PERCENT: 100, // перевод в проценты

  // Surface model
  SURF_DEPTH: 0.012, // глубина для массы узла, м
  SURF_MASS_MIN: 1e-6, // минимальная масса узла, кг
  SURF_WEIGHT_EPS: 1e-9, // epsilon для весов
  SURF_FRICTION_MS_MIN: 0.05, // минимум mu_s
  SURF_FRICTION_MS_MAX: 1.5, // максимум mu_s
  SURF_FRICTION_MK_MIN: 0.03, // минимум mu_k
  SURF_FRICTION_MK_MAX: 1.2, // максимум mu_k
  SURF_KSUM_EPS: 1e-12, // epsilon для сумм жесткости
  SURF_KC_BALL_SCALE: 0.07, // вклад жесткости мяча
  SURF_KC_EN_SCALE: 0.006, // вклад жесткости поверхности
  SURF_KC_SCALE: 0.85, // общий масштаб kc
  SURF_CC_BALL_SCALE: 0.9, // вклад демпфирования мяча
  SURF_CC_TOP_EXP: 0.8, // экспонента для веса cn
  SURF_CC_TOP_WEIGHT: 0.1, // вклад верхнего cn
  SURF_KS_MIN: 600, // минимум ks
  SURF_KS_EN_SCALE: 0.006, // вклад kt в ks
  SURF_KS_TOP_WEIGHT: 0.03, // вклад верхнего kt в ks
  SURF_KBY_MIN: 400, // минимум kby
  SURF_KBY_EN_SCALE: 0.02, // вклад kn в kby
  SURF_CBY_TOP_WEIGHT: 0.25, // вклад cn в cby
  SURF_KLY_MIN: 220, // минимум kly
  SURF_KLY_TOP_EXP: 1.2, // экспонента для веса kn
  SURF_KLY_TOP_SCALE: 0.009, // масштаб для kly
  SURF_CLY_TOP_SCALE: 0.18, // масштаб для cly
  SURF_KBX_MIN: 320, // минимум kbx
  SURF_KBX_EN_SCALE: 0.022, // вклад kt в kbx
  SURF_CBX_TOP_EXP: 0.9, // экспонента для веса ct
  SURF_CBX_TOP_SCALE: 0.28, // масштаб для cbx
  SURF_KLX_MIN: 180, // минимум klx
  SURF_KLX_TOP_EXP: 1.1, // экспонента для веса kt
  SURF_KLX_TOP_SCALE: 0.007, // масштаб для klx
  SURF_CLX_TOP_SCALE: 0.2, // масштаб для clx
  SURF_HP_DEFAULT_PK: 200, // дефолтная жесткость шипов
  SURF_PK_MIN: 8, // минимум pk
  SURF_PK_SCALE: 0.18, // масштаб pk
  SURF_PC_BASE: 2, // базовый коэффициент pc
  SURF_PC_SCALE: 0.014, // масштаб pc
  SURF_PG_SCALE: 0.00016, // масштаб pg
  SURF_FNC_MIN: 8, // минимум fn cap
  SURF_FNC_G_MULT: 60, // множитель g для fn cap
  SURF_GD: 0.9976, // глобальный коэффициент демпфирования
  SURF_LAYER_PH_DEFAULT: 1, // дефолтная высота шипов, мм
  SURF_PIMPL_DENS_MIN: 4, // минимум плотности шипов
  SURF_PIMPL_DENS_DEFAULT: 8, // дефолтная плотность шипов
  SURF_WEIGHT_MS_EXP: 0.9, // экспонента для ms
  SURF_WEIGHT_MK_EXP: 0.9, // экспонента для mk
  SURF_WEIGHT_CN_EXP: 0.8, // экспонента для cn
  SURF_WEIGHT_KT_EXP: 1.0, // экспонента для kt
  SURF_WEIGHT_CN2_EXP: 1.0, // экспонента для cn в cby
  SURF_WEIGHT_KN_EXP: 1.2, // экспонента для kn
  SURF_WEIGHT_CT_EXP: 0.9, // экспонента для ct
  SURF_WEIGHT_KT2_EXP: 1.1, // экспонента для kt (второй набор)
  SURF_DENOM_MIN: 1, // минимум для делителей
  DENOM_MIN: 1, // универсальный минимум для делителей
  SIGN_FALLBACK: 1, // fallback для Math.sign
  SURF_LAYER_MM_TO_M: 0.001, // перевод мм -> м для слоев
  DENS_DEFAULT: 900, // плотность по умолчанию, кг/м3

  // Structural forces
  STRUCT_EDGE_K_FACTOR: 22, // усиление жесткости на краях
  STRUCT_EDGE_C_FACTOR: 6, // усиление демпфирования на краях
  STRUCT_EDGE_GUARD: 2, // крайние узлы спереди
  STRUCT_EDGE_GUARD_BACK: 3, // крайние узлы сзади

  // Rendering
  RENDER_SCALE_BASE: 3900, // базовый масштаб
  RENDER_BOTTOM_MARGIN: 18, // нижний отступ от края canvas
  RENDER_MIN_SURFACE_Y: 140, // минимальная позиция поверхности по Y
  BG_GRID_START: 30, // старт сетки по Y
  BG_GRID_STEP: 36, // шаг сетки по Y
  LAYER_ALPHA: 0.92, // прозрачность слоев
  LAYER_FONT_SIZE: 11, // размер шрифта слоев
  LAYER_LINE_WIDTH: 1.5, // толщина линии слоев
  LAYER_LABEL_X_OFFSET: 4, // смещение подписи X
  LAYER_LABEL_Y_OFFSET: -2, // смещение подписи Y
  LAYER_LABEL_X_OFFSET_M: 0.001, // смещение подписи слоя в метрах
  PIMPL_MIN_COUNT: 8, // минимум количества шипов
  PIMPL_COUNT_SCALE: 2, // масштаб плотности шипов
  PIMPL_INNER_HEIGHT_SCALE: 0.8, // масштаб высоты для шипов внутрь
  PIMPL_LINE_WIDTH: 1.7, // толщина линии шипов
  PRESSURE_R_MIN: 4, // минимум радиуса пятна
  PRESSURE_PMAX_SCALE: 5e5, // масштаб давления
  PRESSURE_ALPHA_MIN: 0.06, // минимум альфы давления
  PRESSURE_ALPHA_MAX: 0.45, // максимум альфы давления
  PRESSURE_GRAD_INNER_R: 2, // внутренний радиус градиента
  PRESSURE_ALPHA_OUT: 0.02, // альфа края давления
  PRESSURE_ELLIPSE_Y_SCALE: 0.35, // сплющивание эллипса
  PATCH_LINE_WIDTH: 3, // толщина линии пятна контакта
  BALL_LINE_WIDTH: 2, // толщина контура мяча
  BALL_MARK_LINE_WIDTH: 2.2, // толщина метки
  BALL_MARK_LEN: 0.82, // длина метки (доля радиуса)
  BALL_MARK_DOT_POS: 0.64, // позиция основной точки
  BALL_MARK_DOT_R: 0.1, // радиус основной точки
  BALL_MARK_DOT2_X: -0.32, // X второй точки
  BALL_MARK_DOT2_Y: 0.24, // Y второй точки
  BALL_MARK_DOT2_R: 0.06, // радиус второй точки
  BALL_GRAD_X: -0.25, // X градиента мяча
  BALL_GRAD_Y: -0.2, // Y градиента мяча
  BALL_GRAD_R: 0.2, // радиус градиента мяча
  SPIN_ARROW_R_PAD: 14, // отступ стрелки спина от мяча
  SPIN_ARROW_A0_POS: 0.3, // начало дуги (CCW)
  SPIN_ARROW_A0_NEG: 2.84, // начало дуги (CW)
  SPIN_ARROW_A1_POS: 2.7, // конец дуги (CCW)
  SPIN_ARROW_A1_NEG: 5.98, // конец дуги (CW)
  SPIN_ARROW_LINE_WIDTH: 1.6, // толщина дуги спина
  SPIN_ARROW_HEAD: 7, // размер головки стрелки
  SPIN_ARROW_HEAD_ANGLE: 0.35, // угол головки стрелки
  VEC_FN_SCALE: 0.0022, // масштаб Fn
  VEC_FT_SCALE: 0.0028, // масштаб Ft
  VEC_V_SCALE: 18, // масштаб скорости v
  VEC_VREL_SCALE: 28, // масштаб относительной скорости
  VEC_LINE_WIDTH: 2, // толщина векторов
  VEC_ARROW_HEAD: 7, // размер стрелки вектора
  VEC_ARROW_ANGLE: 0.42, // угол стрелки вектора
  VEC_LABEL_X_OFFSET: 4, // смещение подписи вектора по X
  VEC_LABEL_Y_OFFSET: -4, // смещение подписи вектора по Y
  HUD_FONT_MAIN: 13, // размер основного шрифта HUD
  HUD_FONT_SUB: 11, // размер вторичного шрифта HUD
  HUD_X: 14, // X позиция HUD
  HUD_T_Y: 22, // Y строки времени
  HUD_OMG_Y: 40, // Y строки omega
  HUD_V_Y: 58, // Y строки скорости
  HUD_NOTE_Y: 76, // Y строки пояснения
  HUD_AXIS_X_LEN: 250, // длина оси X
  HUD_AXIS_Y_LEN: 120, // длина оси Y
  HUD_AXIS_X_LABEL_OFF: 254, // смещение подписи X
  HUD_AXIS_X_LABEL_Y: -2, // смещение подписи X по Y
  HUD_AXIS_Y_LABEL_X: -12, // смещение подписи Y по X
  HUD_AXIS_Y_LABEL_Y: -124, // смещение подписи Y по Y
  HUD_AXIS_X0: -0.074, // x0 для осей HUD
  SCALE_BTN_PERCENT: 100, // множитель процентов для подписи масштаба
  SCALE_BTN_DIGITS: 0, // количество знаков для масштаба

  // Metrics formatting
  METRIC_V_OUT_DIGITS: 3, // знаки для v_out
  METRIC_W_OUT_DIGITS: 2, // знаки для omega_out
  METRIC_A_OUT_DIGITS: 2, // знаки для угла
  METRIC_CONTACT_DIGITS: 2, // знаки для времени контакта
  METRIC_DEF_DIGITS: 3, // знаки для прогиба
  METRIC_SHIFT_DIGITS: 3, // знаки для сдвига
  METRIC_SLIP_DIGITS: 1, // знаки для доли скольжения
  METRIC_ELOSS_DIGITS: 4, // знаки для потерь энергии
  METRIC_J_DIGITS: 4, // знаки для импульсов

  // Compare & charts
  COMPARE_MAX_RUNS: 3, // максимум сохраненных прогонов
  CHART_OMEGA_SCALE: 0.01, // масштаб omega на графике

  // New layer defaults
  NEW_LAYER_T_MM: 1.2, // толщина нового слоя, мм
  NEW_LAYER_KN: 120000, // нормальная жесткость нового слоя
  NEW_LAYER_CN: 28, // нормальное демпфирование нового слоя
  NEW_LAYER_KT: 48000, // касательная жесткость нового слоя
  NEW_LAYER_CT: 20, // касательное демпфирование нового слоя
  NEW_LAYER_MS: 0.72, // mu_s нового слоя
  NEW_LAYER_MK: 0.62, // mu_k нового слоя
  NEW_LAYER_PK: 200, // жесткость шипов нового слоя
  NEW_LAYER_PH: 1, // высота шипов нового слоя, мм

  // Compare table formatting
  COMPARE_V_OUT_DIGITS: 2, // знаки для v_out в сравнении
  COMPARE_W_OUT_DIGITS: 1, // знаки для omega в сравнении
  COMPARE_A_OUT_DIGITS: 1, // знаки для угла в сравнении
  COMPARE_CONTACT_DIGITS: 2, // знаки для времени контакта в сравнении
  COMPARE_DEF_DIGITS: 3, // знаки для прогиба в сравнении
  COMPARE_SLIP_DIGITS: 1, // знаки для скольжения в сравнении

  // Plot
  PLOT_PAD_L: 44, // левый паддинг графика
  PLOT_PAD_R: 8, // правый паддинг графика
  PLOT_PAD_T: 22, // верхний паддинг графика
  PLOT_PAD_B: 26, // нижний паддинг графика
  PLOT_AXIS_WIDTH: 1, // толщина осей графика
  PLOT_LINE_WIDTH: 1.7, // толщина линий графика
  PLOT_FONT_SIZE: 12, // размер шрифта графика
  PLOT_TITLE_X: 8, // X заголовка графика
  PLOT_TITLE_Y: 14, // Y заголовка графика
  PLOT_XMIN_LABEL_OFF: -14, // смещение подписи min X
  PLOT_XMAX_LABEL_OFF: -52, // смещение подписи max X
  PLOT_LABEL_Y_OFF: -8, // смещение подписи по Y
  PLOT_LEGEND_X_START: 100, // старт смещения легенды
  PLOT_LEGEND_X_STEP: 92, // шаг смещения легенды
  PLOT_RANGE_EPS: 1e-8, // epsilon для диапазона графика
  PLOT_FALLBACK_MIN: -1, // минимальный fallback для диапазона
  PLOT_FALLBACK_MAX: 1, // максимальный fallback для диапазона
  PLOT_X_FALLBACK_MIN: 0, // fallback для минимального X
  PLOT_X_FALLBACK_MAX: 1, // fallback для максимального X
  PLOT_X_DIGITS: 3, // знаки для подписей X
  PLOT_LEGEND_BOX_W: 10, // ширина бокса легенды
  PLOT_LEGEND_BOX_H: 8, // высота бокса легенды
  PLOT_LEGEND_Y: 8, // Y позиции легенды
  PLOT_LEGEND_TEXT_X: 14, // X сдвиг текста легенды
  PLOT_LEGEND_TEXT_Y: 15, // Y позиции текста легенды

  // Tick
  MS_TO_S: 0.001, // миллисекунды -> секунды
  TICK_SPAN_EPS: 1e-9, // epsilon для span

  // Checks
  CHECK_VW_EPS: 1e-6, // epsilon для проверки v и omega
  CHECK_ANGLE_1: 15, // тестовый угол 1
  CHECK_ANGLE_2: 60, // тестовый угол 2
  CHECK_ANGLE_DIFF_MIN: 4, // минимум различия углов
  CHECK_SOLID_DIFF_MIN: 0.03, // минимум различия времени контакта
  CHECK_HARD_SCALE: 1.6, // масштаб жесткости для проверки
  CHECK_FRICTION_SCALE: 1.25, // масштаб трения для проверки
  CHECK_SLIP_ALLOW: 4.5, // допустимый прирост скольжения
  CHECK_SPIN_DIFF_MIN: 0.5, // минимум разницы spin

  // Rebound clamp
  REBOUND_EPS: 1e-12, // epsilon для энергии
  REBOUND_VW_EPS: 1e-9 // epsilon для v и omega
};
const mk=(m,t,kn,cn,kt,ct,ms,mk,p,pk,ph)=>({m,t,kn,cn,kt,ct,ms,mk,p,pk,ph,pd:9});
const PRE={classic:[mk("Дерево",2.8,420000,32,180000,18,.42,.32,"none",220,.9),mk("Карбон",.45,980000,14,430000,8,.34,.26,"none",240,.8),mk("Дерево",2.6,410000,28,170000,16,.42,.33,"none",220,.9),mk("Губка",2.0,90000,46,34000,34,.64,.52,"none",180,1),mk("Топшит",1.7,120000,34,56000,28,.95,.81,"out",210,1.2)],inv:[mk("Дерево",2.8,420000,32,180000,18,.42,.32,"none",220,.9),mk("Карбон",.45,980000,14,430000,8,.34,.26,"none",240,.8),mk("Дерево",2.6,410000,28,170000,16,.42,.33,"none",220,.9),mk("Губка",2.1,98000,48,38000,35,.67,.54,"none",190,1),mk("Топшит",1.8,130000,36,62000,30,.97,.84,"in",230,1.2)],hard:[mk("Полимер",2,300000,30,150000,20,.24,.16,"none",200,1),mk("Бетон",20,1300000,10,800000,8,.18,.12,"none",300,.8)]};
const DENS={"Дерево":650,"Карбон":1600,"Губка":280,"Топшит":1100,"Полимер":1200,"Бетон":2300,"Новый":900};
const S={layers:PRE.classic.map(x=>({...x})),res:null,runs:[],anim:{i:0,p:false,raf:0,last:0,simT:0},view:{scale:1,scales:[1,.85,.7,.55],si:0}};
const E={tb:document.querySelector("#layers tbody"),v:document.getElementById("valid"),m:document.getElementById("metrics"),cmp:document.getElementById("cmp"),checks:document.getElementById("checks"),viz:document.getElementById("viz"),sl:document.getElementById("slider"),slLab:document.getElementById("slLabel"),cF:document.getElementById("chartF"),cK:document.getElementById("chartK")};
wire();renderLayers();run();
function wire(){document.getElementById("add").onclick=()=>{S.layers.push(mk("Новый",K.NEW_LAYER_T_MM,K.NEW_LAYER_KN,K.NEW_LAYER_CN,K.NEW_LAYER_KT,K.NEW_LAYER_CT,K.NEW_LAYER_MS,K.NEW_LAYER_MK,"none",K.NEW_LAYER_PK,K.NEW_LAYER_PH));renderLayers();run();};document.getElementById("presetBtn").onclick=()=>{const k=document.getElementById("preset").value;S.layers=PRE[k].map(x=>({...x}));renderLayers();run();};document.getElementById("run").onclick=run;document.getElementById("save").onclick=()=>{if(!S.res)return;S.runs.unshift({l:`${new Date().toLocaleTimeString()} (${val("angle",K.ANGLE_LABEL_FALLBACK)}deg)`,m:S.res.metrics});S.runs=S.runs.slice(0,K.COMPARE_MAX_RUNS);renderCmp();};document.getElementById("scaleBtn").onclick=()=>{S.view.si=(S.view.si+1)%S.view.scales.length;S.view.scale=S.view.scales[S.view.si];document.getElementById("scaleBtn").textContent=`Масштаб: ${(S.view.scale*K.SCALE_BTN_PERCENT).toFixed(K.SCALE_BTN_DIGITS)}%`;if(S.res)draw(S.res.frames[S.anim.i]);};document.getElementById("checkBtn").onclick=checks;E.sl.oninput=()=>{if(!S.res)return;stop();S.anim.i=parseInt(E.sl.value,K.PARSE_INT_BASE)||0;S.anim.simT=S.res.frames[S.anim.i].t;draw(S.res.frames[S.anim.i]);slLabel();};["vVec","vPr","vPatch"].forEach(id=>document.getElementById(id).onchange=()=>S.res&&draw(S.res.frames[S.anim.i]));document.getElementById("animSpeed").oninput=()=>{if(S.anim.p){stop();play();}};const frN=document.getElementById("frMul"),frR=document.getElementById("frMulRange"),syncFr=(v,src)=>{const vv=clamp(parseFloat(v),K.FRICTION_MUL_MIN,K.FRICTION_MUL_MAX);if(src!=="n")frN.value=vv.toFixed(K.FRICTION_MUL_DIGITS);if(src!=="r")frR.value=vv.toFixed(K.FRICTION_MUL_DIGITS);return vv;};frN.onchange=()=>{syncFr(frN.value,"n");run();};frR.oninput=()=>{syncFr(frR.value,"r");run();};E.viz.onclick=()=>{if(!S.res)return;S.anim.p?stop():play();};}
function renderLayers(){E.tb.innerHTML="";S.layers.forEach((l,i)=>{const tr=document.createElement("tr");tr.innerHTML=`<td><button class="mini danger" data-a="x" title="Удалить слой">×</button></td><td><input data-k="m" value="${esc(l.m)}"/></td><td><input data-k="t" type="number" step="${K.LAYER_STEP_T}" value="${l.t}"/></td><td><input data-k="kn" type="number" step="${K.LAYER_STEP_KN}" value="${l.kn}"/></td><td><input data-k="cn" type="number" step="${K.LAYER_STEP_CN}" value="${l.cn}"/></td><td><input data-k="kt" type="number" step="${K.LAYER_STEP_KT}" value="${l.kt}"/></td><td><input data-k="ct" type="number" step="${K.LAYER_STEP_CT}" value="${l.ct}"/></td><td><input data-k="ms" type="number" step="${K.LAYER_STEP_MU}" value="${l.ms}"/></td><td><input data-k="mk" type="number" step="${K.LAYER_STEP_MU}" value="${l.mk}"/></td><td><select data-k="p"><option value="none" ${l.p==="none"?"selected":""}>нет</option><option value="out" ${l.p==="out"?"selected":""}>наружу</option><option value="in" ${l.p==="in"?"selected":""}>внутрь</option></select></td><td><input data-k="pk" type="number" step="${K.LAYER_STEP_PK}" value="${l.pk}"/></td><td><input data-k="ph" type="number" step="${K.LAYER_STEP_PH}" value="${l.ph}"/></td><td><button class="mini" data-a="u" title="Переместить вверх">↑</button><button class="mini" data-a="d" title="Переместить вниз">↓</button></td>`;
tr.querySelectorAll("input,select").forEach(inp=>inp.onchange=()=>{const k=inp.dataset.k;let v=inp.value;if(k!=="m"&&k!=="p")v=parseFloat(v);S.layers[i][k]=v;valid();run();});tr.querySelector("[data-a='u']").onclick=()=>{if(i<1)return;[S.layers[i-1],S.layers[i]]=[S.layers[i],S.layers[i-1]];renderLayers();run();};tr.querySelector("[data-a='d']").onclick=()=>{if(i>=S.layers.length-1)return;[S.layers[i+1],S.layers[i]]=[S.layers[i],S.layers[i+1]];renderLayers();run();};tr.querySelector("[data-a='x']").onclick=()=>{S.layers.splice(i,1);renderLayers();run();};E.tb.appendChild(tr);});valid();}
function valid(){if(S.layers.length<K.LAYERS_MIN_COUNT){E.v.textContent="Нужен минимум 1 слой";E.v.style.color="#a3271c";return false;}for(const l of S.layers){if(!(l.t>K.LAYER_MIN_THICKNESS&&l.kn>K.LAYER_MIN_STIFFNESS&&l.cn>=K.LAYER_MIN_DAMPING&&l.kt>K.LAYER_MIN_STIFFNESS&&l.ct>=K.LAYER_MIN_DAMPING&&l.ms>K.LAYER_MIN_MU&&l.mk>K.LAYER_MIN_MU&&l.mk<=l.ms)){E.v.textContent="Проверьте диапазоны: t>0, k>0, c>=0, mu_k<=mu_s";E.v.style.color="#a3271c";return false;}}E.v.textContent="Слои валидны";E.v.style.color="#2f6a28";return true;}
function input(){const sp=Math.max(K.SPEED_MIN,val("speed",K.SPEED_DEFAULT));const ad=clamp(val("angle",K.ANGLE_DEFAULT_DEG),K.ANGLE_MIN_DEG,K.ANGLE_MAX_DEG);const sps=val("spin",K.SPIN_DEFAULT_RPS)*parseFloat(document.getElementById("spinDir").value);const bt=document.getElementById("ballType").value;const frMul=clamp(val("frMul",K.FRICTION_MUL_MIN),K.FRICTION_MUL_MIN,K.FRICTION_MUL_MAX);document.getElementById("frMul").value=frMul.toFixed(K.FRICTION_MUL_DIGITS);document.getElementById("frMulRange").value=frMul.toFixed(K.FRICTION_MUL_DIGITS);return{q:document.getElementById("quality").value,col:{sp,ad,w:sps*K.TAU},ball:{r:clamp(val("radius",K.BALL_RADIUS_DEFAULT_MM),K.BALL_RADIUS_MIN_MM,K.BALL_RADIUS_MAX_MM)*K.MM_TO_M,m:bt==="h"?K.BALL_MASS_HOLLOW:K.BALL_MASS_SOLID,if:bt==="h"?K.BALL_INERTIA_HOLLOW:K.BALL_INERTIA_SOLID,k:Math.max(K.BALL_K_MIN,val("ballK",K.BALL_K_DEFAULT)),c:Math.max(K.BALL_C_MIN,val("ballC",K.BALL_C_DEFAULT))},frMul,viewScale:S.view.scale||K.VIEW_SCALE_DEFAULT,layers:S.layers.map(x=>({...x}))};}
function run(){if(!valid())return;const r=sim(input());S.res=r;S.anim.i=0;S.anim.simT=r.frames.length?r.frames[0].t:0;metrics(r.metrics);renderCmp();charts(r);E.sl.max=Math.max(0,r.frames.length-1);E.sl.value="0";draw(r.frames[0]);slLabel();play();}
function sim(inp){
const dt=inp.q==="h"?K.SIM_DT_HIGH:K.SIM_DT_NORMAL,fdt=inp.q==="h"?K.SIM_FRAME_DT_HIGH:K.SIM_FRAME_DT_NORMAL,maxT=K.SIM_MAX_T,n=inp.q==="h"?K.SIM_N_HIGH:K.SIM_N_NORMAL,hw=K.SIM_HALF_WIDTH,dx=2*hw/(n-1);
const x=new Float64Array(n);for(let i=0;i<n;i++)x[i]=-hw+i*dx;
const uy=new Float64Array(n),ux=new Float64Array(n),vy=new Float64Array(n),vx=new Float64Array(n),stick=new Float64Array(n),th=new Float64Array(n),thv=new Float64Array(n);
const top=inp.layers.slice().reverse(),s=surf(inp.layers,dx,inp.ball,inp.frMul),ang=inp.col.ad*K.DEG_TO_RAD;
const viewScale=inp.viewScale||K.VIEW_SCALE_DEFAULT;
const vx0=inp.col.sp*Math.cos(ang),vy0=-Math.max(K.SIM_MIN_VY_IN,inp.col.sp*Math.sin(ang));
const tPreScale=K.PRECONTACT_PX/(K.RENDER_SCALE_BASE*viewScale*Math.max(inp.col.sp,K.SPEED_MIN));
const tPre=Math.min(K.PRECONTACT_TIME_MAX,tPreScale);
const b={x:-vx0*tPre,y:inp.ball.r- vy0*tPre+K.HALF*K.GRAVITY*tPre*tPre,vx:vx0,vy:vy0,w:inp.col.w,p:0};
const I=inp.ball.if*inp.ball.m*inp.ball.r*inp.ball.r,g=K.GRAVITY;
const t=[],fnA=[],ftA=[],defA=[],slA=[],wA=[],vxA=[],vyA=[],frames=[];
const v0=Math.hypot(b.vx,b.vy),w0=Math.abs(b.w);
let tm=0,nf=0,start=false,noC=0,tEnd=0,maxDef=0,maxShift=0,slipT=0,JN=0,JT=0,ke0=KE(b,inp.ball.m,I);
const uxLim=Math.max(dx*K.SIM_UX_LIM_FACTOR,K.SIM_UX_LIM_MIN),uyLim=K.SIM_UY_LIM,fnCap=Math.max(K.SIM_FN_CAP_MIN,inp.ball.m*(Math.abs(inp.col.sp*Math.sin(ang))+K.SIM_FN_CAP_VY_BIAS)/dt*K.SIM_FN_CAP_FACTOR),keCap=ke0*K.SIM_KE_CAP_FACTOR;
while(tm<maxT){
const fy=new Float64Array(n),fx=new Float64Array(n),fth=new Float64Array(n),cfy=new Float64Array(n),cfx=new Float64Array(n),cfth=new Float64Array(n);
structForces(fy,fx,uy,vy,ux,vx,s,n);
let FN=0,FT=0,TQ=0,cN=0,pc=0,pw=0,pr=0,pmax=0,sl=0;
const ci=clamp(Math.round((b.x+hw)/dx),0,n-1),sr=Math.ceil(inp.ball.r/dx)+K.SIM_CONTACT_RADIUS_EXTRA,i0=Math.max(0,ci-sr),i1=Math.min(n-1,ci+sr);
for(let i=i0;i<=i1;i++){
const sx=x[i]+ux[i],sy=uy[i],dd=b.x-sx;if(Math.abs(dd)>=inp.ball.r*K.SIM_CONTACT_R_MARGIN)continue;
const cc=inp.ball.r*inp.ball.r-dd*dd;if(cc<=0)continue;
const yb=b.y-Math.sqrt(cc),pen=sy-yb;
if(pen<=0){stick[i]*=K.SIM_STICK_DECAY;continue;}
start=true;cN++;
const prt=-(b.vy-vy[i]);
let fn=Math.max(0,s.kc*Math.pow(pen,K.SIM_HERTZ_EXP)+s.cc*Math.max(0,prt));
fn=Math.min(fn,s.fnc);
const vr=(b.vx-b.w*inp.ball.r)-vx[i];
stick[i]+=vr*dt;
const ms=s.ms*(1+K.SIM_TILT_MS_GAIN*Math.min(1,Math.abs(th[i]))),mk=s.mk*(1+K.SIM_TILT_MK_GAIN*Math.min(1,Math.abs(th[i])));
const ftt=-s.ks*stick[i],lim=ms*fn;
let ft;
if(Math.abs(ftt)<=lim){ft=ftt;}else{ft=-Math.sign(vr||K.SIGN_FALLBACK)*mk*fn;stick[i]=-ft/Math.max(K.DENOM_MIN,s.ks);slipT+=dt;}
if(s.hp){cfth[i]+=s.pg*ft*(top[0].p==="out"?1:K.SIM_TILT_OUT_SCALE);ft*=1+K.SIM_TILT_FORCE_GAIN*Math.abs(th[i]);}
cfy[i]-=fn;cfx[i]-=ft;FN+=fn;FT+=ft;TQ+=ft*inp.ball.r;
const p=fn/Math.max(K.SIM_PRESSURE_EPS,dx*K.SIM_PRESSURE_DX_SCALE);if(p>pmax)pmax=p;
pc+=sx*fn;pw+=fn;pr=Math.max(pr,Math.abs(dd));sl+=Math.abs(vr);
}
if(FN>fnCap){
const q=fnCap/FN;FN*=q;FT*=q;TQ*=q;pmax*=q;
for(let i=0;i<n;i++){cfy[i]*=q;cfx[i]*=q;cfth[i]*=q;}
}
for(let i=0;i<n;i++){fy[i]+=cfy[i];fx[i]+=cfx[i];fth[i]+=cfth[i];}
if(pw>0)pc/=pw;else pc=b.x;
if(cN>0)noC=0;else if(start)noC++;
for(let i=0;i<n;i++){
if(s.hp){const a=fth[i]-s.pk*th[i]-s.pc*thv[i];thv[i]+=a*dt;th[i]=clamp(th[i]+thv[i]*dt,-K.SIM_THETA_CLAMP,K.SIM_THETA_CLAMP);}else{thv[i]*=K.SIM_THETA_DAMP;th[i]*=K.SIM_THETA_DAMP;}
const ay=fy[i]/s.m,ax=fx[i]/s.m;
vy[i]=clamp((vy[i]+ay*dt)*s.gd,-K.SIM_NODE_V_CLAMP,K.SIM_NODE_V_CLAMP);vx[i]=clamp((vx[i]+ax*dt)*s.gd,-K.SIM_NODE_V_CLAMP,K.SIM_NODE_V_CLAMP);
uy[i]=clamp(uy[i]+vy[i]*dt,-uyLim,K.SIM_UY_MAX);ux[i]=clamp(ux[i]+vx[i]*dt,-uxLim,uxLim);
maxDef=Math.max(maxDef,-uy[i]);maxShift=Math.max(maxShift,Math.abs(ux[i]));
}
const axb=FT/inp.ball.m,ayb=FN/inp.ball.m-g;
b.vx+=axb*dt;b.vy+=ayb*dt;b.x+=b.vx*dt;b.y+=b.vy*dt;b.w+=(-TQ/I)*dt;b.p+=b.w*dt;
const keNow=KE(b,inp.ball.m,I);if(keNow>keCap){const sE=Math.sqrt(keCap/Math.max(K.SIM_ENERGY_EPS,keNow));b.vx*=sE;b.vy*=sE;b.w*=sE;}
JN+=FN*dt;JT+=FT*dt;
const sll=cN?sl/cN:0;
t.push(tm);fnA.push(FN);ftA.push(FT);defA.push(maxDef*K.M_TO_MM);slA.push(sll);wA.push(b.w);vxA.push(b.vx);vyA.push(b.vy);
if(tm>=nf){frames.push(frame(tm,b,uy,ux,th,{ph:"contact",FN,FT,pc,pr,pmax,sll,lf:s.lf,x}));nf+=fdt;}
if(start&&noC>K.SIM_NO_CONTACT_BREAK&&b.y>inp.ball.r+K.SIM_DETACH_Y_MARGIN&&b.vy>K.SIM_DETACH_VY_THRESHOLD){tEnd=tm;break;}
tm+=dt;
}
if(tEnd<=0)tEnd=tm;
const sep=clampRebound({x:b.x,y:b.y,p:b.p,vx:b.vx,vy:b.vy,w:b.w},v0,w0,ke0,inp.ball.m,I);
b.x=sep.x;b.y=sep.y;b.p=sep.p;b.vx=sep.vx;b.vy=sep.vy;b.w=sep.w;
const keSep=KE(sep,inp.ball.m,I),vOutSep=Math.hypot(sep.vx,sep.vy),aOutSep=Math.atan2(sep.vy,sep.vx)*K.RAD_TO_DEG,wOutSep=sep.w;
const pDur=K.SIM_POST_DUR,df=fdt;
let pt=0;
while(pt<=pDur){
const fy=new Float64Array(n),fx=new Float64Array(n);
structForces(fy,fx,uy,vy,ux,vx,s,n);
for(let i=0;i<n;i++){
if(s.hp){const a=-s.pk*th[i]-s.pc*thv[i];thv[i]+=a*df;th[i]=clamp(th[i]+thv[i]*df,-K.SIM_THETA_CLAMP,K.SIM_THETA_CLAMP);}
const ay=fy[i]/s.m,ax=fx[i]/s.m;
vy[i]=clamp((vy[i]+ay*df)*s.gd,-K.SIM_NODE_V_CLAMP,K.SIM_NODE_V_CLAMP);vx[i]=clamp((vx[i]+ax*df)*s.gd,-K.SIM_NODE_V_CLAMP,K.SIM_NODE_V_CLAMP);
uy[i]=clamp(uy[i]+vy[i]*df,-uyLim,K.SIM_UY_MAX);ux[i]=clamp(ux[i]+vx[i]*df,-uxLim,uxLim);
}
b.vy-=g*df;b.w*=Math.max(0,1-K.SIM_SPIN_AIR_DAMP*df);b.x+=b.vx*df;b.y+=b.vy*df;b.p+=b.w*df;
const at=tEnd+pt;
t.push(at);fnA.push(0);ftA.push(0);defA.push(Math.max(...uy.map(v=>-v))*K.M_TO_MM);slA.push(0);wA.push(b.w);vxA.push(b.vx);vyA.push(b.vy);
if(at>=nf){frames.push(frame(at,b,uy,ux,th,{ph:"flight",FN:0,FT:0,pc:b.x,pr:0,pmax:0,sll:0,lf:s.lf,x}));nf+=fdt;}
pt+=df;
}
return{frames,t,fnA,ftA,defA,slA,wA,vxA,vyA,metrics:{vOut:vOutSep,wOut:wOutSep,aOut:aOutSep,cMs:tEnd*K.S_TO_MS,dMm:maxDef*K.M_TO_MM,shMm:maxShift*K.M_TO_MM,sl:(slipT/Math.max(tEnd,K.SIM_SLIP_TIME_EPS))*K.PERCENT,eLoss:Math.max(0,ke0-keSep),JN,JT}};
}
function surf(ls,dx,b,frMul){
const tp=ls.slice().reverse(),cN=tp.map(l=>(l.t*K.SURF_LAYER_MM_TO_M)/Math.max(K.SURF_DENOM_MIN,l.kn)),cT=tp.map(l=>(l.t*K.SURF_LAYER_MM_TO_M)/Math.max(K.SURF_DENOM_MIN,l.kt)),sN=cN.reduce((a,v)=>a+v,0),sT=cT.reduce((a,v)=>a+v,0),top=tp[0];
const depth=K.SURF_DEPTH,mArea=tp.reduce((a,l)=>a+((DENS[l.m]||K.DENS_DEFAULT)*(l.t*K.SURF_LAYER_MM_TO_M)),0),m=Math.max(K.SURF_MASS_MIN,mArea*dx*depth);
const w=(k,p)=>{let a=0,s=0;for(let i=0;i<tp.length;i++){const ww=Math.exp(-i*p);a+=tp[i][k]*ww;s+=ww;}return a/Math.max(K.SURF_WEIGHT_EPS,s);};
const baseMs=w("ms",K.SURF_WEIGHT_MS_EXP),baseMk=w("mk",K.SURF_WEIGHT_MK_EXP),ms=clamp(baseMs*frMul,K.SURF_FRICTION_MS_MIN,K.SURF_FRICTION_MS_MAX),mk=clamp(baseMk*frMul,K.SURF_FRICTION_MK_MIN,Math.min(ms,K.SURF_FRICTION_MK_MAX)),keN=1/Math.max(K.SURF_KSUM_EPS,sN),keT=1/Math.max(K.SURF_KSUM_EPS,sT),kc=(b.k*K.SURF_KC_BALL_SCALE+keN*K.SURF_KC_EN_SCALE)*K.SURF_KC_SCALE,cc=b.c*K.SURF_CC_BALL_SCALE+w("cn",K.SURF_WEIGHT_CN_EXP)*K.SURF_CC_TOP_WEIGHT,ks=Math.max(K.SURF_KS_MIN,keT*K.SURF_KS_EN_SCALE+w("kt",K.SURF_WEIGHT_KT_EXP)*K.SURF_KS_TOP_WEIGHT),kby=Math.max(K.SURF_KBY_MIN,keN*K.SURF_KBY_EN_SCALE),cby=w("cn",K.SURF_WEIGHT_CN2_EXP)*K.SURF_CBY_TOP_WEIGHT,kly=Math.max(K.SURF_KLY_MIN,w("kn",K.SURF_WEIGHT_KN_EXP)*K.SURF_KLY_TOP_SCALE),cly=w("cn",K.SURF_WEIGHT_KN_EXP)*K.SURF_CLY_TOP_SCALE,kbx=Math.max(K.SURF_KBX_MIN,keT*K.SURF_KBX_EN_SCALE),cbx=w("ct",K.SURF_WEIGHT_CT_EXP)*K.SURF_CBX_TOP_SCALE,klx=Math.max(K.SURF_KLX_MIN,w("kt",K.SURF_WEIGHT_KT2_EXP)*K.SURF_KLX_TOP_SCALE),clx=w("ct",K.SURF_WEIGHT_KT2_EXP)*K.SURF_CLX_TOP_SCALE,hp=top.p!=="none",pk=Math.max(K.SURF_PK_MIN,(top.pk||K.SURF_HP_DEFAULT_PK)*K.SURF_PK_SCALE),pc=K.SURF_PC_BASE+K.SURF_PC_SCALE*(top.pk||K.SURF_HP_DEFAULT_PK),pg=K.SURF_PG_SCALE*(hp?1:0),fnc=Math.max(K.SURF_FNC_MIN,b.m*K.GRAVITY*K.SURF_FNC_G_MULT);
let cn=0,ct=0;const lf=[];
for(let i=0;i<tp.length;i++){const l=tp[i],ty=1-cn/Math.max(K.SURF_KSUM_EPS,sN),tx=1-ct/Math.max(K.SURF_KSUM_EPS,sT);cn+=cN[i];ct+=cT[i];const by=1-cn/Math.max(K.SURF_KSUM_EPS,sN),bx=1-ct/Math.max(K.SURF_KSUM_EPS,sT);lf.push({m:l.m,t:l.t*K.SURF_LAYER_MM_TO_M,ty:clamp(ty,0,1),by:clamp(by,0,1),tx:clamp(tx,0,1),bx:clamp(bx,0,1),p:l.p,ph:(l.ph||K.SURF_LAYER_PH_DEFAULT)*K.SURF_LAYER_MM_TO_M,pd:Math.max(K.SURF_PIMPL_DENS_MIN,l.pd||K.SURF_PIMPL_DENS_DEFAULT)});}
return{m,ms,mk,kc,cc,ks,kby,cby,kly,cly,kbx,cbx,klx,clx,hp,pk,pc,pg,lf,fnc,gd:K.SURF_GD};
}
function structForces(fy,fx,uy,vy,ux,vx,s,n){const ek=s.kby*K.STRUCT_EDGE_K_FACTOR,ec=s.cby*K.STRUCT_EDGE_C_FACTOR;for(let i=0;i<n;i++){fy[i]+=-s.kby*uy[i]-s.cby*vy[i];fx[i]+=-s.kbx*ux[i]-s.cbx*vx[i];if(i>0){fy[i]+=s.kly*(uy[i-1]-uy[i])+s.cly*(vy[i-1]-vy[i]);fx[i]+=s.klx*(ux[i-1]-ux[i])+s.clx*(vx[i-1]-vx[i]);}if(i<n-1){fy[i]+=s.kly*(uy[i+1]-uy[i])+s.cly*(vy[i+1]-vy[i]);fx[i]+=s.klx*(ux[i+1]-ux[i])+s.clx*(vx[i+1]-vx[i]);}if(i<K.STRUCT_EDGE_GUARD||i>n-K.STRUCT_EDGE_GUARD_BACK){fy[i]+=-ek*uy[i]-ec*vy[i];fx[i]+=-ek*ux[i]-ec*vx[i];}}}
function frame(t,b,uy,ux,th,e){return{t,ph:e.ph,b:{x:b.x,y:b.y,vx:b.vx,vy:b.vy,w:b.w,p:b.p},FN:e.FN,FT:e.FT,pc:e.pc,pr:e.pr,pmax:e.pmax,sll:e.sll,x:Array.from(e.x),uy:Array.from(uy),ux:Array.from(ux),th:Array.from(th),lf:e.lf};}
function draw(f){if(!f)return;const ctx=E.viz.getContext("2d"),w=E.viz.width,h=E.viz.height;ctx.clearRect(0,0,w,h);const sc=S.view.scale||K.VIEW_SCALE_DEFAULT,scalePx=K.RENDER_SCALE_BASE*sc,layerDepth=f.lf.reduce((a,l)=>a+l.t,0)*scalePx;const ox=w*K.HALF,oy=Math.max(K.RENDER_MIN_SURFACE_Y,h-K.RENDER_BOTTOM_MARGIN-layerDepth);const W={s:scalePx,ox,oy};bg(ctx,w,h);layers(ctx,f,W);if(document.getElementById("vPr").checked&&f.pr>0)pressure(ctx,f,W);if(document.getElementById("vPatch").checked&&f.pr>0)patch(ctx,f,W);ball(ctx,f,W,input().ball.r);if(document.getElementById("vVec").checked)vecs(ctx,f,W);hud(ctx,f,W);} 
function P(x,y,W){return{x:W.ox+x*W.s,y:W.oy-y*W.s};}
function bg(ctx,w,h){const g=ctx.createLinearGradient(0,0,0,h);g.addColorStop(0,"#fff9ee");g.addColorStop(1,"#f3e7d2");ctx.fillStyle=g;ctx.fillRect(0,0,w,h);ctx.strokeStyle="rgba(77,67,50,.16)";for(let y=K.BG_GRID_START;y<h;y+=K.BG_GRID_STEP){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}}
function layers(ctx,f,W){const pal=["#ae4a2c","#f0b975","#cabd9a","#5e7388","#c69e6f","#85735d"],xL=f.x[0],xR=f.x[f.x.length-1];let d=0;for(let li=0;li<f.lf.length;li++){const lf=f.lf[li],td=d,bd=d-lf.t;d=bd;const a=P(xL,td,W),b=P(xR,td,W),c=P(xR,bd,W),e=P(xL,bd,W);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.lineTo(c.x,c.y);ctx.lineTo(e.x,e.y);ctx.closePath();ctx.fillStyle=pal[li%pal.length];ctx.globalAlpha=K.LAYER_ALPHA;ctx.fill();ctx.globalAlpha=1;ctx.strokeStyle="rgba(48,35,25,.6)";ctx.stroke();if(li===0&&lf.p!=="none")pimples(ctx,lf,td,W,xL,xR);const lb=P(xL+K.LAYER_LABEL_X_OFFSET_M,(td+bd)*K.HALF,W);ctx.fillStyle="rgba(27,22,17,.75)";ctx.font=`${K.LAYER_FONT_SIZE}px IBM Plex Sans`;ctx.fillText(lf.m,lb.x+K.LAYER_LABEL_X_OFFSET,lb.y+K.LAYER_LABEL_Y_OFFSET);}const s0=P(xL,0,W),s1=P(xR,0,W);ctx.strokeStyle="#3a2d22";ctx.lineWidth=K.LAYER_LINE_WIDTH;ctx.beginPath();ctx.moveTo(s0.x,s0.y);ctx.lineTo(s1.x,s1.y);ctx.stroke();}
function pimples(ctx,lf,td,W,xL,xR){const cnt=Math.max(K.PIMPL_MIN_COUNT,Math.floor(lf.pd*K.PIMPL_COUNT_SCALE)),step=(xR-xL)/cnt,h=lf.ph*(lf.p==="out"?1:K.PIMPL_INNER_HEIGHT_SCALE);ctx.strokeStyle=lf.p==="out"?"#6e2c1a":"#4f2f1d";ctx.lineWidth=K.PIMPL_LINE_WIDTH;for(let i=1;i<cnt;i++){const x=xL+i*step;const p0=P(x,td,W);const p1=lf.p==="out"?P(x,td+h,W):P(x,td-h,W);ctx.beginPath();ctx.moveTo(p0.x,p0.y);ctx.lineTo(p1.x,p1.y);ctx.stroke();}}
function pressure(ctx,f,W){const c=P(f.pc,0,W),r=Math.max(K.PRESSURE_R_MIN,f.pr*W.s),a=clamp(f.pmax/K.PRESSURE_PMAX_SCALE,K.PRESSURE_ALPHA_MIN,K.PRESSURE_ALPHA_MAX),g=ctx.createRadialGradient(c.x,c.y,K.PRESSURE_GRAD_INNER_R,c.x,c.y,r);g.addColorStop(0,`rgba(186,50,24,${a})`);g.addColorStop(1,`rgba(186,50,24,${K.PRESSURE_ALPHA_OUT})`);ctx.fillStyle=g;ctx.beginPath();ctx.ellipse(c.x,c.y,r,r*K.PRESSURE_ELLIPSE_Y_SCALE,0,0,K.TAU);ctx.fill();}
function patch(ctx,f,W){const l=P(f.pc-f.pr,0,W),r=P(f.pc+f.pr,0,W);ctx.strokeStyle="#7b2417";ctx.lineWidth=K.PATCH_LINE_WIDTH;ctx.beginPath();ctx.moveTo(l.x,l.y);ctx.lineTo(r.x,r.y);ctx.stroke();}
function ball(ctx,f,W,rw){const c=P(f.b.x,f.b.y,W),r=rw*W.s;ctx.save();ctx.translate(c.x,c.y);const g=ctx.createRadialGradient(r*K.BALL_GRAD_X,r*K.BALL_GRAD_Y,r*K.BALL_GRAD_R,0,0,r);g.addColorStop(0,"#fefefb");g.addColorStop(1,"#ebebe6");ctx.fillStyle=g;ctx.strokeStyle="#49433b";ctx.lineWidth=K.BALL_LINE_WIDTH;ctx.beginPath();ctx.arc(0,0,r,0,K.TAU);ctx.fill();ctx.stroke();ctx.rotate(f.b.p);ctx.strokeStyle="#bf3e1e";ctx.lineWidth=K.BALL_MARK_LINE_WIDTH;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(r*K.BALL_MARK_LEN,0);ctx.stroke();ctx.fillStyle="#bf3e1e";ctx.beginPath();ctx.arc(r*K.BALL_MARK_DOT_POS,0,r*K.BALL_MARK_DOT_R,0,K.TAU);ctx.fill();ctx.beginPath();ctx.arc(r*K.BALL_MARK_DOT2_X,r*K.BALL_MARK_DOT2_Y,r*K.BALL_MARK_DOT2_R,0,K.TAU);ctx.fill();ctx.restore();spinArr(ctx,c.x,c.y,r,f.b.w);} 
function spinArr(ctx,x,y,r,w){const s=w>=0?1:-1,rr=r+K.SPIN_ARROW_R_PAD,a0=s>0?K.SPIN_ARROW_A0_POS:K.SPIN_ARROW_A0_NEG,a1=s>0?K.SPIN_ARROW_A1_POS:K.SPIN_ARROW_A1_NEG;ctx.strokeStyle="#7f2d17";ctx.lineWidth=K.SPIN_ARROW_LINE_WIDTH;ctx.beginPath();ctx.arc(x,y,rr,a0,a1,s<0);ctx.stroke();const e=s>0?a1:a0,ex=x+rr*Math.cos(e),ey=y+rr*Math.sin(e);ctx.fillStyle="#7f2d17";ctx.beginPath();ctx.moveTo(ex,ey);ctx.lineTo(ex-K.SPIN_ARROW_HEAD*Math.cos(e-K.SPIN_ARROW_HEAD_ANGLE),ey-K.SPIN_ARROW_HEAD*Math.sin(e-K.SPIN_ARROW_HEAD_ANGLE));ctx.lineTo(ex-K.SPIN_ARROW_HEAD*Math.cos(e+K.SPIN_ARROW_HEAD_ANGLE),ey-K.SPIN_ARROW_HEAD*Math.sin(e+K.SPIN_ARROW_HEAD_ANGLE));ctx.closePath();ctx.fill();}
function vecs(ctx,f,W){const c=P(f.b.x,f.b.y,W);V(ctx,c.x,c.y,0,-f.FN*K.VEC_FN_SCALE,"#1d5f79","Fn");V(ctx,c.x,c.y,f.FT*K.VEC_FT_SCALE,0,"#b44617","Ft");V(ctx,c.x,c.y,f.b.vx*K.VEC_V_SCALE,-f.b.vy*K.VEC_V_SCALE,"#316f29","v");if(f.pr>0){const p=P(f.pc,0,W);V(ctx,p.x,p.y,f.sll*K.VEC_VREL_SCALE,0,"#5d2f7a","v_rel");}}
function V(ctx,x,y,dx,dy,col,txt){ctx.strokeStyle=col;ctx.fillStyle=col;ctx.lineWidth=K.VEC_LINE_WIDTH;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+dx,y+dy);ctx.stroke();const a=Math.atan2(dy,dx||K.TICK_SPAN_EPS),ex=x+dx,ey=y+dy;ctx.beginPath();ctx.moveTo(ex,ey);ctx.lineTo(ex-K.VEC_ARROW_HEAD*Math.cos(a-K.VEC_ARROW_ANGLE),ey-K.VEC_ARROW_HEAD*Math.sin(a-K.VEC_ARROW_ANGLE));ctx.lineTo(ex-K.VEC_ARROW_HEAD*Math.cos(a+K.VEC_ARROW_ANGLE),ey-K.VEC_ARROW_HEAD*Math.sin(a+K.VEC_ARROW_ANGLE));ctx.closePath();ctx.fill();ctx.font=`${K.HUD_FONT_SUB}px IBM Plex Sans`;ctx.fillText(txt,ex+K.VEC_LABEL_X_OFFSET,ey+K.VEC_LABEL_Y_OFFSET);} 
function hud(ctx,f,W){ctx.fillStyle="#2a231a";ctx.font=`${K.HUD_FONT_MAIN}px IBM Plex Sans`;ctx.fillText(`t = ${(f.t*K.S_TO_MS).toFixed(K.METRIC_CONTACT_DIGITS)} ms (${f.ph})`,K.HUD_X,K.HUD_T_Y);ctx.fillText(`omega = ${f.b.w.toFixed(K.METRIC_W_OUT_DIGITS)} rad/s (${f.b.w>=0?"CCW":"CW"})`,K.HUD_X,K.HUD_OMG_Y);ctx.fillText(`vx=${f.b.vx.toFixed(K.METRIC_W_OUT_DIGITS)} m/s, vy=${f.b.vy.toFixed(K.METRIC_W_OUT_DIGITS)} m/s`,K.HUD_X,K.HUD_V_Y);ctx.fillStyle="rgba(41,31,22,.8)";ctx.font=`${K.HUD_FONT_SUB}px IBM Plex Sans`;ctx.fillText("Деформация поверхности не визуализируется (слои показываются статически)",K.HUD_X,K.HUD_NOTE_Y);const o=P(K.HUD_AXIS_X0,0,W);ctx.strokeStyle="rgba(40,31,23,.55)";ctx.beginPath();ctx.moveTo(o.x,o.y);ctx.lineTo(o.x+K.HUD_AXIS_X_LEN,o.y);ctx.moveTo(o.x,o.y);ctx.lineTo(o.x,o.y-K.HUD_AXIS_Y_LEN);ctx.stroke();ctx.fillText("x",o.x+K.HUD_AXIS_X_LABEL_OFF,o.y+K.HUD_AXIS_X_LABEL_Y);ctx.fillText("y",o.x+K.HUD_AXIS_Y_LABEL_X,o.y+K.HUD_AXIS_Y_LABEL_Y);} 
function metrics(m){const rows=[["v_out (после контакта), м/с",m.vOut.toFixed(K.METRIC_V_OUT_DIGITS)],["omega_out (после контакта), рад/с",m.wOut.toFixed(K.METRIC_W_OUT_DIGITS)],["угол выхода, °",m.aOut.toFixed(K.METRIC_A_OUT_DIGITS)],["контакт, мс",m.cMs.toFixed(K.METRIC_CONTACT_DIGITS)],["макс. прогиб, мм",m.dMm.toFixed(K.METRIC_DEF_DIGITS)],["макс. сдвиг, мм",m.shMm.toFixed(K.METRIC_SHIFT_DIGITS)],["доля скольжения, %",m.sl.toFixed(K.METRIC_SLIP_DIGITS)],["потери энергии, Дж",m.eLoss.toFixed(K.METRIC_ELOSS_DIGITS)],["импульс Jn",m.JN.toFixed(K.METRIC_J_DIGITS)],["импульс Jt",m.JT.toFixed(K.METRIC_J_DIGITS)]];E.m.innerHTML=rows.map(([k,v])=>`<div class="m"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");}
function renderCmp(){if(!S.runs.length){E.cmp.innerHTML=`<p>Сохраните до ${K.COMPARE_MAX_RUNS} прогонов для сравнения.</p>`;return;}let h="<table><thead><tr><th>Run</th><th>v_out</th><th>omega</th><th>angle</th><th>contact ms</th><th>def mm</th><th>slip %</th></tr></thead><tbody>";S.runs.forEach(r=>{h+=`<tr><td>${esc(r.l)}</td><td>${r.m.vOut.toFixed(K.COMPARE_V_OUT_DIGITS)}</td><td>${r.m.wOut.toFixed(K.COMPARE_W_OUT_DIGITS)}</td><td>${r.m.aOut.toFixed(K.COMPARE_A_OUT_DIGITS)}</td><td>${r.m.cMs.toFixed(K.COMPARE_CONTACT_DIGITS)}</td><td>${r.m.dMm.toFixed(K.COMPARE_DEF_DIGITS)}</td><td>${r.m.sl.toFixed(K.COMPARE_SLIP_DIGITS)}</td></tr>`;});h+="</tbody></table>";E.cmp.innerHTML=h;}
function charts(r){plot(E.cF,r.t,[{y:r.fnA,c:"#1d5f79",n:"Fn"},{y:r.ftA,c:"#b44617",n:"Ft"}],"Силы");plot(E.cK,r.t,[{y:r.defA,c:"#7a317f",n:"def(mm)"},{y:r.slA,c:"#3d6f29",n:"slip"},{y:r.wA.map(w=>w*K.CHART_OMEGA_SCALE),c:"#704d32",n:`omega*${K.CHART_OMEGA_SCALE}`},{y:r.vxA,c:"#29517e",n:"vx"},{y:r.vyA,c:"#a63a32",n:"vy"}],"Кинематика");}
function plot(cv,tx,lns,title){const c=cv.getContext("2d"),w=cv.width,h=cv.height,p={l:K.PLOT_PAD_L,r:K.PLOT_PAD_R,t:K.PLOT_PAD_T,b:K.PLOT_PAD_B};c.clearRect(0,0,w,h);c.fillStyle="#fffdf7";c.fillRect(0,0,w,h);const xmin=tx[0]||K.PLOT_X_FALLBACK_MIN,xmax=tx[tx.length-1]||K.PLOT_X_FALLBACK_MAX;let ymin=Infinity,ymax=-Infinity;for(const l of lns){for(const v of l.y){ymin=Math.min(ymin,v);ymax=Math.max(ymax,v);}}if(!Number.isFinite(ymin)||!Number.isFinite(ymax)||ymin===ymax){ymin=K.PLOT_FALLBACK_MIN;ymax=K.PLOT_FALLBACK_MAX;}const sx=x=>p.l+((x-xmin)/Math.max(K.PLOT_RANGE_EPS,xmax-xmin))*(w-p.l-p.r),sy=y=>h-p.b-((y-ymin)/Math.max(K.PLOT_RANGE_EPS,ymax-ymin))*(h-p.t-p.b);c.strokeStyle="#9e8f74";c.lineWidth=K.PLOT_AXIS_WIDTH;c.beginPath();c.moveTo(p.l,p.t);c.lineTo(p.l,h-p.b);c.lineTo(w-p.r,h-p.b);c.stroke();for(const l of lns){c.strokeStyle=l.c;c.lineWidth=K.PLOT_LINE_WIDTH;c.beginPath();for(let i=0;i<tx.length;i++){const x=sx(tx[i]),y=sy(l.y[i]);if(i===0)c.moveTo(x,y);else c.lineTo(x,y);}c.stroke();}c.fillStyle="#2b2419";c.font=`${K.PLOT_FONT_SIZE}px IBM Plex Sans`;c.fillText(title,K.PLOT_TITLE_X,K.PLOT_TITLE_Y);c.fillText(`${xmin.toFixed(K.PLOT_X_DIGITS)}s`,p.l+K.PLOT_XMIN_LABEL_OFF,h+K.PLOT_LABEL_Y_OFF);c.fillText(`${xmax.toFixed(K.PLOT_X_DIGITS)}s`,w+K.PLOT_XMAX_LABEL_OFF,h+K.PLOT_LABEL_Y_OFF);let lx=w-K.PLOT_LEGEND_X_START;for(const l of lns){c.fillStyle=l.c;c.fillRect(lx,K.PLOT_LEGEND_Y,K.PLOT_LEGEND_BOX_W,K.PLOT_LEGEND_BOX_H);c.fillStyle="#2b2419";c.fillText(l.n,lx+K.PLOT_LEGEND_TEXT_X,K.PLOT_LEGEND_TEXT_Y);lx-=K.PLOT_LEGEND_X_STEP;}}
function play(){if(!S.res||S.anim.p)return;S.anim.p=true;S.anim.last=0;S.anim.raf=requestAnimationFrame(tick);}
function stop(){S.anim.p=false;if(S.anim.raf)cancelAnimationFrame(S.anim.raf);}
function tick(ts){
if(!S.anim.p||!S.res)return;
const f=S.res.frames;if(!f.length)return;
if(!S.anim.last)S.anim.last=ts;
const d=(ts-S.anim.last)*K.MS_TO_S;
S.anim.last=ts;
const sp=parseFloat(document.getElementById("animSpeed").value);
const t0=f[0].t,t1=f[f.length-1].t,span=Math.max(K.TICK_SPAN_EPS,t1-t0);
S.anim.simT+=d*sp;
while(S.anim.simT>t1)S.anim.simT-=span;
while(S.anim.simT<t0)S.anim.simT+=span;
S.anim.i=frameIdxByTime(f,S.anim.simT);
draw(f[S.anim.i]);
E.sl.value=String(S.anim.i);
slLabel();
S.anim.raf=requestAnimationFrame(tick);
}
function frameIdxByTime(fr,tv){let lo=0,hi=fr.length-1;while(lo<hi){const mid=(lo+hi+1)>>1;if(fr[mid].t<=tv)lo=mid;else hi=mid-1;}return lo;}
function slLabel(){const m=S.res?S.res.frames.length-1:0;E.slLab.textContent=`${S.anim.i} / ${m}`;}
function checks(){const out=[],b=input(),br=sim(b);out.push(ok(br.metrics.cMs>0&&Number.isFinite(br.metrics.vOut),"Базовый расчет стабилен"));out.push(ok(!(br.metrics.vOut>b.col.sp+K.CHECK_VW_EPS&&Math.abs(br.metrics.wOut)>Math.abs(b.col.w)+K.CHECK_VW_EPS),"Нет одновременного роста v и |omega|"));const a1=sim({...b,col:{...b.col,ad:K.CHECK_ANGLE_1}}),a2=sim({...b,col:{...b.col,ad:K.CHECK_ANGLE_2}});out.push(ok(Math.abs(a1.metrics.aOut-a2.metrics.aOut)>K.CHECK_ANGLE_DIFF_MIN,"Угол входа влияет на траекторию"));const solid={...b,ball:{...b.ball,m:K.BALL_MASS_SOLID,if:K.BALL_INERTIA_SOLID}},sr=sim(solid);out.push(ok(Math.abs(sr.metrics.cMs-br.metrics.cMs)>K.CHECK_SOLID_DIFF_MIN,"Полый/сплошной различимы"));const hard={...b,layers:b.layers.map(l=>({...l,kn:l.kn*K.CHECK_HARD_SCALE,kt:l.kt*K.CHECK_HARD_SCALE}))},hr=sim(hard);out.push(ok(hr.metrics.dMm<br.metrics.dMm,"Рост жесткости уменьшает прогиб"));const fr={...b,layers:b.layers.map(l=>({...l,ms:l.ms*K.CHECK_FRICTION_SCALE,mk:l.mk*K.CHECK_FRICTION_SCALE}))},frR=sim(fr);out.push(ok(frR.metrics.sl<=br.metrics.sl+K.CHECK_SLIP_ALLOW,"Рост трения ограничивает скольжение"));const lo=b.layers.map(x=>({...x}));lo[lo.length-1].p="out";const li=b.layers.map(x=>({...x}));li[li.length-1].p="in";const ro=sim({...b,layers:lo}),ri=sim({...b,layers:li});out.push(ok(Math.abs(ro.metrics.wOut-ri.metrics.wOut)>K.CHECK_SPIN_DIFF_MIN,"Шипы наружу/внутрь меняют spin"));E.checks.textContent=out.join("\n");}
function clampRebound(st,v0,w0,ke0,m,I){let vx=st.vx,vy=st.vy,w=st.w;const eps=K.REBOUND_EPS;let v=Math.hypot(vx,vy),aw=Math.abs(w),ke=K.HALF*m*v*v+K.HALF*I*aw*aw;if(ke>ke0){const s=Math.sqrt(ke0/Math.max(eps,ke));vx*=s;vy*=s;w*=s;v*=s;aw*=s;}if(v>v0+K.REBOUND_VW_EPS&&aw>w0+K.REBOUND_VW_EPS){const keepV=v-v0<=aw-w0;if(keepV){aw=w0;w=Math.sign(w||K.SIGN_FALLBACK)*aw;const vMax=Math.sqrt(Math.max(0,(ke0-K.HALF*I*aw*aw)*K.TWO/m));if(v>vMax){const sv=vMax/Math.max(eps,v);vx*=sv;vy*=sv;v=vMax;}}else{const sv=v0/Math.max(eps,v);vx*=sv;vy*=sv;v=v0;const wMax=Math.sqrt(Math.max(0,(ke0-K.HALF*m*v*v)*K.TWO/I));if(aw>wMax){aw=wMax;w=Math.sign(w||K.SIGN_FALLBACK)*aw;}}}return{...st,vx,vy,w};}
function ok(c,t){return`${c?"OK":"FAIL"}: ${t}`;}function KE(b,m,I){return K.HALF*m*(b.vx*b.vx+b.vy*b.vy)+K.HALF*I*b.w*b.w;}function val(id,f){const v=parseFloat(document.getElementById(id).value);return Number.isFinite(v)?v:f;}function esc(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");}function clamp(v,a,b){return Math.max(a,Math.min(b,v));}
})();

