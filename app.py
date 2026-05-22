import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# הגדרות עיצוב מתקדמות ומראה מקצועי מותאם למובייל ולמחשב כאחד
st.set_page_config(page_title="מערכת ניתוח מניות Pro", layout="wide", initial_sidebar_state="collapsed")

# הזרקת קוד CSS למצב חשוך (Dark Mode) מלא וקבוע בכל המכשירים, ושולי גלילה נוחים במובייל
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    /* כפייה אגרסיבית של רקע כהה לכל חלקי האתר בכל מכשיר (מחשב + נייד) */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        font-family: 'Inter', sans-serif;
        background-color: #131722 !important;
        color: #d1d4dc !important;
    }
    
    /* שולי מגן בצדדים למניעת תקיעת גלילה במובייל */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
    }
    
    .rtl-container {
        direction: rtl;
        text-align: right;
    }
    
    /* התאמות צבעי טקסט וכותרות למצב חשוך */
    h1, h2, h3, h4, h5, h6, p, label, [data-testid="stMarkdownContainer"] p {
        color: #e0e3eb !important;
    }
    
    /* עיצוב כפתורי הטווחים (1D, 5D, 1M...) כפתורי אגודל מעוצבים */
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 5px !important;
    }
    
    div[data-testid="stRadio"] label {
        background-color: #1c2030 !important;
        color: #9db2c6 !important;
        padding: 5px 12px !important;
        border-radius: 6px !important;
        border: 1px solid #2a2e39 !important;
        font-weight: 600 !important;
        font-size: 12px !important;
    }
    
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: #2962ff !important;
        color: white !important;
        border-color: #2962ff !important;
    }
    
    /* עיצוב הטאבים למצב חשוך */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1c2030 !important;
        border-bottom: 1px solid #2a2e39 !important;
        padding: 2px;
        border-radius: 6px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #787b86 !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #e0e3eb !important;
        background-color: #2a2e39 !important;
        border-radius: 4px;
    }
    
    /* קלט טקסט כהה */
    input[type="text"] {
        background-color: #1c2030 !important;
        color: #ffffff !important;
        border: 1px solid #2a2e39 !important;
    }
    </style>
""", unsafe_allow_html=True)

# פונקציית עזר לעיצוב מספרים גדולים (כולל מספרים שליליים)
def format_large_num(num):
    if num is None or pd.isna(num): return "N/A"
    is_negative = num < 0
    abs_num = abs(num)
    
    if abs_num >= 1e12: txt = f"${abs_num/1e12:.2f}T"
    elif abs_num >= 1e9: txt = f"${abs_num/1e9:.2f}B"
    elif abs_num >= 1e6: txt = f"${abs_num/1e6:.2f}M"
    else: txt = f"${abs_num:,.0f}"
        
    return f"-{txt}" if is_negative else txt

# פונקציה לעיצוב אחוזים רגילים שמגיעים כעשרוני (כמו רווח גולמי ותפעולי)
def format_pct_raw(val):
    if val is None or pd.isna(val): return "N/A"
    # אם הנתון כבר הוכפל (גדול מ-1) נציג כפי שהוא, אחרת נכפיל ב-100
    if abs(val) > 1.0:
        return f"{val:.2f}%"
    return f"{val * 100:.2f}%"

# פונקציה ייעודית לחילוץ אמין של תשואת דיבידנד מ-Yahoo Finance
def format_dividend(val):
    if val is None or pd.isna(val) or val == 0: return "N/A"
    # Yahoo Finance מחזיר לרוב את תשואת הדיבידנד כערך עשרוני קטן (למשל 0.0055 עבור 0.55%)
    if val < 1.0:
        return f"{val * 100:.2f}%"
    return f"{val:.2f}%"

# פונקציה לחישוב מתנד RSI
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# כותרת עליונה קומפקטית
st.markdown("<div class='rtl-container'><h3 style='margin-bottom:0; color:#ffffff;'>📈 Stock Analyzer Pro</h3></div>", unsafe_allow_html=True)

# שורת קלט עליונה
ticker = st.text_input("הכנס טיקר:", "AAPL").upper().strip()

if ticker:
    # כפתורי בחירת טווח מאוחדים בשורה אחת בראש העמוד המשפיעים על שני הטאבים
    global_timeframe = st.radio(
        "בחר טווח זמן לניתוח:", 
        ["1D", "5D", "1M", "6M", "1Y", "YTD", "3Y", "5Y"], 
        index=2, 
        key="global_tf"
    )
    
    is_intraday = global_timeframe in ["1D", "5D"]
    
    with st.spinner('מחלץ ומחשב נתונים...'):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or 'longName' not in info:
                st.error(f"לא נמצאו נתונים עבור הטיקר: {ticker}")
                st.stop()
                
            company_name = info.get('longName', ticker)
            sector = info.get('sector', 'לא ידוע')
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            st.markdown(f"""
                <div class='rtl-container' style='background-color:#1c2030; padding:10px; border-radius:6px; margin-bottom:15px; border: 1px solid #2a2e39; font-size:13px;'>
                    <b style='color:#ffffff;'>{company_name} ({ticker})</b> | סקטור: {sector} | מחיר: <b style='color:#2962ff;'>${current_price:.2f}</b>
                </div>
            """, unsafe_allow_html=True)
            
            tf_mapping = {
                "1D": {"period": "1d", "interval": "5m"}, "5D": {"period": "5d", "interval": "15m"},
                "1M": {"period": "1mo", "interval": "1d"}, "6M": {"period": "6mo", "interval": "1d"},
                "1Y": {"period": "1y", "interval": "1d"}, "YTD": {"period": "ytd", "interval": "1d"},
                "3Y": {"period": "3y", "interval": "1d"}, "5Y": {"period": "5y", "interval": "1d"}
            }
            opts = tf_mapping[global_timeframe]
            
            try:
                df_fund_chart = stock.history(period=opts["period"], interval=opts["interval"])
            except Exception:
                df_fund_chart = stock.history(period=opts["period"])
            
            try:
                df_ref_3m = stock.history(period="3mo", interval="1d")
                vol_ma_3m_global = df_ref_3m['Volume'].mean() if not df_ref_3m.empty else 0
            except Exception:
                vol_ma_3m_global = 0
                
            df_tech = pd.DataFrame()
            if is_intraday:
                try:
                    df_tech = stock.history(period=global_timeframe.lower(), interval=opts["interval"])
                except Exception:
                    df_tech = pd.DataFrame()
                if not df_tech.empty:
                    df_tech['MA_Fast'] = df_tech['Close'].ewm(span=9, adjust=False).mean()
                    df_tech['MA_Slow'] = df_tech['Close'].ewm(span=21, adjust=False).mean()
                    df_tech['RSI'] = calculate_rsi(df_tech['Close'], period=14)
                    df_tech['Vol_MA_3M'] = df_tech['Volume'].rolling(window=20).mean()
                    fast_label, slow_label, vol_label = "EMA 9", "EMA 21", "ממוצע נפח (20)"
            else:
                try:
                    df_full = stock.history(period="5y", interval="1d")
                except Exception:
                    df_full = pd.DataFrame()
                if not df_full.empty:
                    df_full['MA_Fast'] = df_full['Close'].rolling(window=50).mean()
                    df_full['MA_Slow'] = df_full['Close'].rolling(window=150).mean()
                    df_full['RSI'] = calculate_rsi(df_full['Close'], period=14)
                    df_full['Vol_MA_3M'] = df_full['Volume'].rolling(window=63).mean()
                    fast_label, slow_label, vol_label = "SMA 50", "SMA 150", "ממוצע נפח 3M (נע)"
                    
                    last_date = df_full.index[-1]
                    if global_timeframe == "1M": start_date = last_date - pd.Timedelta(days=30)
                    elif global_timeframe == "6M": start_date = last_date - pd.Timedelta(days=182)
                    elif global_timeframe == "1Y": start_date = last_date - pd.Timedelta(days=365)
                    elif global_timeframe == "YTD": start_date = pd.Timestamp(year=last_date.year, month=1, day=1, tz=last_date.tz)
                    elif global_timeframe == "3Y": start_date = last_date - pd.Timedelta(days=365*3)
                    else: start_date = df_full.index[0]
                    df_tech = df_full.loc[start_date:].copy()

            tab1, tab2 = st.tabs(["🔍 ניתוח פנדמנטלי", "📊 ניתוח טכני"])
            
            # ==========================================
            # טאב 1: ניתוח פנדמנטלי (תיקון סופי לתצוגת האחוזים)
            # ==========================================
            with tab1:
                col_graph, col_id = st.columns([2.0, 1.0])
                
                with col_graph:
                    if not df_fund_chart.empty:
                        fig_fund = go.Figure()
                        fig_fund.add_trace(go.Scatter(x=df_fund_chart.index, y=df_fund_chart['Close'], mode='lines', name='מחיר', line=dict(color='#2962ff', width=2)))
                        fig_fund.update_layout(
                            hovermode='x unified', dragmode=False, height=360,
                            template="plotly_dark", paper_bgcolor='#131722', plot_bgcolor='#131722',
                            margin=dict(l=5, r=5, t=5, b=5)
                        )
                        st.plotly_chart(fig_fund, use_container_width=True, config={'scrollZoom': False, 'displayModeBar': False})
                
                with col_id:
                    market_cap = info.get('marketCap')
                    operating_cf = info.get('operatingCashflow')
                    free_cash_flow = info.get('freeCashflow')
                    pe = info.get('trailingPE')
                    fwd_pe = info.get('forwardPE')
                    peg = info.get('pegRatio')
                    p_cf = (market_cap / operating_cf) if market_cap and operating_cf else info.get('priceToCashFlow')
                    
                    earnings_yield = (1 / pe) * 100 if pe else None
                    col_cf_yield = (operating_cf / market_cap) * 100 if operating_cf and market_cap else None
                    fcf_yield = (free_cash_flow / market_cap) * 100 if free_cash_flow and market_cap else None
                    
                    # שימוש בפונקציות הייעודיות החדשות למניעת עיוות נתוני דיבידנד
                    div_yield = info.get('dividendYield')
                    payout_ratio = info.get('payoutRatio')
                    
                    total_cash = info.get('totalCash')
                    total_debt = info.get('totalDebt')
                    net_balance = (total_cash - total_debt) if total_cash is not None and total_debt is not None else None

                    st.markdown(f"""
                    <div class='rtl-container' style='font-size:11px; line-height:1.4; border:1px solid #2a2e39; padding:10px; border-radius:6px; background-color:#1c2030; height:360px; overflow-y:auto;'>
                        <b style='font-size:13px; color:#ffffff;'>📋 נתונים פיננסיים</b><hr style='margin:4px 0; border-color:#2a2e39;'>
                        
                        <span style='color:#2962ff; font-weight:700;'>💰 Financials</span>
                        <table style='width:100%; margin-bottom:6px; color:#b2b5be;'>
                            <tr><td>Market Cap:</td><td style='text-align:left; color:#ffffff;'>{format_large_num(market_cap)}</td></tr>
                            <tr><td>P/CF:</td><td style='text-align:left; color:#ffffff;'>{f'{p_cf:.2f}' if p_cf else 'N/A'}</td></tr>
                            <tr><td>P/E / Forward P/E:</td><td style='text-align:left; color:#ffffff;'>{f'{pe:.1f}' if pe else 'N/A'} / {f'{fwd_pe:.1f}' if fwd_pe else 'N/A'}</td></tr>
                            <tr><td>PEG Ratio:</td><td style='text-align:left; color:#ffffff;'>{f'{peg:.2f}' if peg else 'N/A'}</td></tr>
                        </table>
                        
                        <span style='color:#2962ff; font-weight:700;'>📈 Yields</span>
                        <table style='width:100%; margin-bottom:6px; color:#b2b5be;'>
                            <tr><td>Earnings Yield:</td><td style='text-align:left; color:#ffffff;'>{f'{earnings_yield:.1f}%' if earnings_yield else 'N/A'}</td></tr>
                            <tr><td>C/F Yield / FCF Yield:</td><td style='text-align:left; color:#ffffff;'>{f'{col_cf_yield:.1f}%' if col_cf_yield else 'N/A'} / {f'{fcf_yield:.1f}%' if fcf_yield else 'N/A'}</td></tr>
                            <tr><td>Dividend / Payout:</td><td style='text-align:left; color:#ffffff;'>{format_dividend(div_yield)} / {format_pct_raw(payout_ratio)}</td></tr>
                        </table>
                        
                        <span style='color:#2962ff; font-weight:700;'>⚖️ Balances</span>
                        <table style='width:100%; margin-bottom:6px; color:#b2b5be;'>
                            <tr><td>Total Cash / Debt:</td><td style='text-align:left; color:#ffffff;'>{format_large_num(total_cash)} / {format_large_num(total_debt)}</td></tr>
                            <tr><td>Net Balance:</td><td style='text-align:left; color:#ffffff;'>{format_large_num(net_balance)}</td></tr>
                        </table>
                        
                        <span style='color:#2962ff; font-weight:700;'>📊 Margins</span>
                        <table style='width:100%; color:#b2b5be;'>
                            <tr><td>Gross Margin:</td><td style='text-align:left; color:#ffffff;'>{format_pct_raw(info.get('grossMargins'))}</td></tr>
                            <tr><td>Operating / Net Margin:</td><td style='text-align:left; color:#ffffff;'>{format_pct_raw(info.get('operatingMargins'))} / {format_pct_raw(info.get('profitMargins'))}</td></tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("---")
                st.subheader("📋 כרטיס ניקוד אוטומטי")
                roe = info.get('returnOnEquity')
                rev_growth = info.get('revenueGrowth')
                current_ratio = info.get('currentRatio')
                
                if roe and roe >= 0.15: st.success(f"✅ **ROE:** {roe*100:.1f}% (מעל היעד של 15%)")
                else: st.error(f"❌ **ROE:** {f'{roe*100:.1f}%' if roe else 'N/A'} (מתחת ליעד)")
                if rev_growth and rev_growth > 0: st.success(f"✅ **צמיחת הכנסות:** {rev_growth*100:.1f}%")
                else: st.error(f"❌ **צמיחת הכנסות שלילית או חסרה**")
                if current_ratio and current_ratio >= 1: st.success(f"✅ **יחס שוטף:** {current_ratio:.2f} (נזילות בריאה)")
                else: st.error(f"❌ **יחס שוטף נמוך מ-1**")

            # ==========================================
            # טאב 2: ניתוח טכני
            # ==========================================
            with tab2:
                if df_tech.empty:
                    st.error("אין מספיק נתונים לטווח זה.")
                else:
                    df_tech = df_tech.copy()
                    df_tech['display_time'] = df_tech.index.strftime('%H:%M') if is_intraday else df_tech.index.strftime('%Y-%m-%d')
                    time_list = df_tech['display_time'].tolist()
                    
                    start_idx, end_idx = st.select_slider(
                        "מדוד תשואה ב-LIVE ישירות על הבר (גרור את האצבע):",
                        options=range(len(time_list)),
                        value=(0, len(time_list)-1),
                        format_func=lambda x: time_list[x],
                        key="tech_slider_live"
                    )
                    
                    p1 = df_tech['Close'].iloc[start_idx]
                    p2 = df_tech['Close'].iloc[end_idx]
                    pct_diff = ((p2 - p1) / p1) * 100
                    price_diff = p2 - p1
                    
                    t1_val = df_tech.index[start_idx]
                    t2_val = df_tech.index[end_idx]

                    badge_color = "#10b981" if pct_diff >= 0 else "#ef4444"
                    badge_bg = "rgba(16, 185, 129, 0.15)" if pct_diff >= 0 else "rgba(239, 68, 68, 0.15)"
                    sign = "+" if pct_diff >= 0 else ""
                    
                    st.markdown(f"""
                        <div class='rtl-container' style='display: flex; gap: 15px; background-color: #1c2030; padding: 6px 12px; border-radius: 4px; border: 1px solid #2a2e39; font-size: 12px; align-items: center;'>
                            <span style='color: #787b86;'>שינוי מחיר: <b style='color:#ffffff;'>${price_diff:.2f}</b></span>
                            <span style='background-color: {badge_bg}; color: {badge_color}; padding: 2px 8px; border-radius: 4px; font-weight: bold;'>תשואה: {sign}{pct_diff:.2f}%</span>
                        </div>
                    """, unsafe_allow_html=True)

                    fig_tech = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.55, 0.22, 0.23])
                    
                    fig_tech.add_trace(go.Candlestick(
                        x=df_tech.index, open=df_tech['Open'], high=df_tech['High'], low=df_tech['Low'], close=df_tech['Close'],
                        name='מחיר',
                        increasing=dict(line=dict(color='#089981'), fillcolor='#089981'),
                        decreasing=dict(line=dict(color='#f23645'), fillcolor='#f23645')
                    ), row=1, col=1)
                    
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA_Fast'], mode='lines', name=fast_label, line=dict(color='#ff9f43', width=1.5)), row=1, col=1)
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA_Slow'], mode='lines', name=slow_label, line=dict(color='#2196f3', width=1.5)), row=1, col=1)
                    
                    colors, opacities = [], []
                    for _, row in df_tech.iterrows():
                        is_bullish = row['Close'] >= row['Open']
                        colors.append('#089981' if is_bullish else '#f23645')
                        if not pd.isna(row['Vol_MA_3M']) and row['Volume'] >= row['Vol_MA_3M']:
                            opacities.append(0.9)
                        else:
                            opacities.append(0.25)
                    
                    fig_tech.add_trace(go.Bar(x=df_tech.index, y=df_tech['Volume'], name='ווליום', marker=dict(color=colors, opacity=opacities), showlegend=False), row=2, col=1)
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Vol_MA_3M'], mode='lines', name=vol_label, line=dict(color='#2962ff', width=1.8)), row=2, col=1)
                    
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['RSI'], mode='lines', name='RSI', line=dict(color='#9c27b0', width=1.5)), row=3, col=1)
                    fig_tech.add_shape(type="line", x0=df_tech.index[0], y0=70, x1=df_tech.index[-1], y1=70, line=dict(color="#f23645", width=1, dash="dash"), row=3, col=1)
                    fig_tech.add_shape(type="line", x0=df_tech.index[0], y0=30, x1=df_tech.index[-1], y1=30, line=dict(color="#089981", width=1, dash="dash"), row=3, col=1)
                    
                    fig_tech.add_vrect(x0=t1_val, x1=t2_val, fillcolor="#2962ff", opacity=0.08, layer="below", line_width=0, row="all", col=1)
                    
                    fig_tech.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', spikethickness=1, spikedash='solid', spikecolor='#434651')
                    fig_tech.update_layout(
                        hovermode='x unified' if not is_intraday else False, 
                        dragmode=False, xaxis_rangeslider_visible=False, height=600,
                        template="plotly_dark", paper_bgcolor='#131722', plot_bgcolor='#131722',
                        margin=dict(l=5, r=5, t=5, b=5),
                        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=10, color='#d1d4dc'))
                    )
                    
                    st.plotly_chart(fig_tech, use_container_width=True, config={'scrollZoom': False, 'displayModeBar': False})
                    
        except Exception as e:
            st.error(f"שגיאה בעיבוד הנתונים: {e}")
