import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# הגדרות עיצוב מתקדמות ומראה מקצועי מותאם למובייל
st.set_page_config(page_title="מערכת ניתוח מניות Pro", layout="wide", initial_sidebar_state="collapsed")

# הזרקת קוד CSS מותאם אישית למראה נקי, מקצועי ותמיכה ביישור לימין (RTL) לחלקים בעברית
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [data-testid="stSidebarUserContent"] {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
    }
    
    /* התאמות מיוחדות למובייל - צמצום מרווחים */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    .rtl-container {
        direction: rtl;
        text-align: right;
    }
    
    /* עיצוב כפתורי הרדיו שיראו כמו כפתורי טאץ' מקצועיים */
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
    }
    
    div[data-testid="stRadio"] label {
        background-color: #f1f5f9 !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: #0f172a !important;
        color: white !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 22px;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# פונקציית עזר לעיצוב מספרים גדולים
def format_large_num(num):
    if num is None or pd.isna(num): return "N/A"
    if num >= 1e12: return f"${num/1e12:.2f}T"
    if num >= 1e9: return f"${num/1e9:.2f}B"
    if num >= 1e6: return f"${num/1e6:.2f}M"
    return f"${num:,.0f}"

# פונקציית עזר לעיצוב אחוזים
def format_pct(val):
    if val is None or pd.isna(val): return "N/A"
    return f"{val * 100:.2f}%" if val <= 1.0 else f"{val:.2f}%"

# פונקציה לחישוב מתנד RSI
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# כותרת ראשית בעיצוב נקי
st.markdown("<div class='rtl-container'><h2 style='margin-bottom:0;'>📈 Stock Analyzer Pro</h2><p style='color:#64748b; font-size:14px; margin-top:0;'>גרסת מובייל מלוטשת לניתוח טכני ופנדמנטלי בהשראת TradingView</p></div>", unsafe_allow_html=True)

# תיבת קלט מעוצבת
ticker = st.text_input("הכנס טיקר (MSFT, AAPL, PANW):", "AAPL").upper().strip()

if ticker:
    with st.spinner('מחלץ נתונים מ-Yahoo Finance...'):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or 'longName' not in info:
                st.error(f"לא נמצאו נתונים עבור הטיקר: {ticker}. ודא שהקשדת נכון.")
                st.stop()
                
            company_name = info.get('longName', ticker)
            sector = info.get('sector', 'לא ידוע')
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            # תצוגת שורת סטטוס עליונה מקצועית ומצומצמת למובייל
            st.markdown(f"""
                <div class='rtl-container' style='background-color:#f8f9fa; padding:10px; border-radius:8px; margin-bottom:15px; border: 1px solid #e9ecef; font-size:14px;'>
                    <b>{company_name} ({ticker})</b> | סקטור: {sector} | מחיר: <b style='color:#0f172a;'>${current_price:.2f}</b>
                </div>
            """, unsafe_allow_html=True)
            
            # יצירת הטאבים
            tab1, tab2 = st.tabs(["🔍 אנליזה פנדמנטלית ותעודת זהות", "📊 חדר ניתוח טכני"])
            
            # ==========================================
            # טאב 1: ניתוח פנדמנטלי + תעודת זהות מלאה (חסינת חיתוך מסך)
            # ==========================================
            with tab1:
                col_graph, col_id = st.columns([1.6, 1.4])
                
                with col_graph:
                    timeframe_fund = st.radio("טווח גרף מהיר:", ["1D", "5D", "1M", "6M", "1Y", "YTD", "3Y", "5Y"], index=4, key="fund_tf")
                    tf_mapping_fund = {
                        "1D": {"period": "1d", "interval": "5m"}, "5D": {"period": "5d", "interval": "15m"},
                        "1M": {"period": "1mo", "interval": "1d"}, "6M": {"period": "6mo", "interval": "1d"},
                        "1Y": {"period": "1y", "interval": "1d"}, "YTD": {"period": "ytd", "interval": "1d"},
                        "3Y": {"period": "3y", "interval": "1d"}, "5Y": {"period": "5y", "interval": "1d"}
                    }
                    opts_f = tf_mapping_fund[timeframe_fund]
                    
                    try:
                        df_fund_chart = stock.history(period=opts_f["period"], interval=opts_f["interval"])
                    except Exception:
                        df_fund_chart = stock.history(period=opts_f["period"])
                        
                    if not df_fund_chart.empty:
                        fig_fund = go.Figure()
                        fig_fund.add_trace(go.Scatter(x=df_fund_chart.index, y=df_fund_chart['Close'], mode='lines', name='מחיר סגירה', line=dict(color='#0f172a', width=2)))
                        fig_fund.update_layout(hovermode='x unified', dragmode=False, height=300, template="plotly_white", margin=dict(l=5, r=5, t=5, b=5))
                        st.plotly_chart(fig_fund, use_container_width=True, config={'scrollZoom': False, 'displayModeBar': False})
                
                with col_id:
                    # שימוש בטבלה נקייה ורספונסיבית כדי להציג את כל הנתונים בלי שייחתכו בנייד
                    st.markdown(f"""
                    <div class='rtl-container' style='font-size:13px; line-height:1.6; border:1px solid #e2e8f0; padding:12px; border-radius:8px;'>
                        <b style='font-size:15px; color:#0f172a;'>🪪 תעודת זהות פנדמנטלית מלאה</b><hr style='margin:8px 0;'>
                        <table style='width:100%; border-collapse: collapse;'>
                            <tr><td><b>Market Cap:</b></td><td style='text-align:left;'>{format_large_num(info.get('marketCap'))}</td></tr>
                            <tr><td><b>P/E Ratio (TTM):</b></td><td style='text-align:left;'>{f"{info.get('trailingPE', 0):.1f}" if info.get('trailingPE') else 'N/A'}</td></tr>
                            <tr><td><b>Forward P/E:</b></td><td style='text-align:left;'>{f"{info.get('forwardPE', 0):.1f}" if info.get('forwardPE') else 'N/A'}</td></tr>
                            <tr><td><b>PEG Ratio:</b></td><td style='text-align:left;'>{f"{info.get('pegRatio', 0):.2f}" if info.get('pegRatio') else 'N/A'}</td></tr>
                            <tr><td><b>Operating Cash Flow:</b></td><td style='text-align:left;'>{format_large_num(info.get('operatingCashflow'))}</td></tr>
                            <tr><td><b>Free Cash Flow:</b></td><td style='text-align:left;'>{format_large_num(info.get('freeCashflow'))}</td></tr>
                            <tr><td><b>Total Cash (MRQ):</b></td><td style='text-align:left;'>{format_large_num(info.get('totalCash'))}</td></tr>
                            <tr><td><b>Total Debt (MRQ):</b></td><td style='text-align:left;'>{format_large_num(info.get('totalDebt'))}</td></tr>
                            <tr><td><b>Gross Margin:</b></td><td style='text-align:left;'>{format_pct(info.get('grossMargins'))}</td></tr>
                            <tr><td><b>Return on Equity (ROE):</b></td><td style='text-align:left;'>{f"{info.get('returnOnEquity', 0)*100:.1f}%" if info.get('returnOnEquity') else 'N/A'}</td></tr>
                            <tr><td><b>צמיחת הכנסות:</b></td><td style='text-align:left;'>{f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else 'N/A'}</td></tr>
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
            # טאב 2: ניתוח טכני מתקדם (תיקון באג ה-"Line" וקו ממוצע ווליום דינמי)
            # ==========================================
            with tab2:
                timeframe_tech = st.radio("בחר טווח זמן לניתוח:", ["1D", "5D", "1M", "6M", "1Y", "YTD", "3Y", "5Y"], index=4, key="tech_tf")
                
                is_intraday = timeframe_tech in ["1D", "5D"]
                
                if is_intraday:
                    interval = "5m" if timeframe_tech == "1D" else "15m"
                    df_tech = stock.history(period=timeframe_tech.lower(), interval=interval)
                    if not df_tech.empty:
                        df_tech['MA_Fast'] = df_tech['Close'].ewm(span=9, adjust=False).mean()
                        df_tech['MA_Slow'] = df_tech['Close'].ewm(span=21, adjust=False).mean()
                        df_tech['RSI'] = calculate_rsi(df_tech['Close'], period=14)
                        # לתוך היום ממוצע הווליום מחושב מקומית על פני 20 נרות
                        df_tech['Vol_MA_3M'] = df_tech['Volume'].rolling(window=20).mean()
                        fast_label, slow_label = "EMA 9", "EMA 21"
                        vol_label = "ממוצע נפח נע (20)"
                else:
                    # תמיד מושכים 5 שנים כדי שהממוצעים ארוכי הטווח יחושבו במלואם
                    df_full = stock.history(period="5y", interval="1d")
                    if not df_full.empty:
                        df_full['MA_Fast'] = df_full['Close'].rolling(window=50).mean()
                        df_full['MA_Slow'] = df_full['Close'].rolling(window=150).mean()
                        df_full['RSI'] = calculate_rsi(df_full['Close'], period=14)
                        
                        # תיקון: ממוצע ווליום דינמי שמשתנה לאורך הגרף (SMA 63 המשקף 3 חודשי מסחר)
                        df_full['Vol_MA_3M'] = df_full['Volume'].rolling(window=63).mean()
                        
                        fast_label, slow_label = "SMA 50", "SMA 150"
                        vol_label = "ממוצע נפח 3 חודשים (נע)"
                        
                        last_date = df_full.index[-1]
                        if timeframe_tech == "1M": start_date = last_date - pd.Timedelta(days=30)
                        elif timeframe_tech == "6M": start_date = last_date - pd.Timedelta(days=182)
                        elif timeframe_tech == "1Y": start_date = last_date - pd.Timedelta(days=365)
                        elif timeframe_tech == "YTD": start_date = pd.Timestamp(year=last_date.year, month=1, day=1, tz=last_date.tz)
                        elif timeframe_tech == "3Y": start_date = last_date - pd.Timedelta(days=365*3)
                        else: start_date = df_full.index[0]
                        df_tech = df_full.loc[start_date:].copy()
                    else:
                        df_tech = pd.DataFrame()
                
                if df_tech.empty:
                    st.error("לא נמצאו נתונים לטווח שנבחר.")
                else:
                    # ==========================================
                    # 📏 מנוע המדידה ומחשבון האחוזים (לפני הגרף כדי להזריק את ההצללה)
                    # ==========================================
                    st.markdown("<div class='rtl-container'><h4>📏 מחשבון אחוזים ומדידת טווח (סגנון TradingView)</h4></div>", unsafe_allow_html=True)
                    
                    if is_intraday:
                        df_tech['display_time'] = df_tech.index.strftime('%H:%M')
                    else:
                        df_tech['display_time'] = df_tech.index.strftime('%Y-%m-%d')
                        
                    time_list = df_tech['display_time'].tolist()
                    
                    start_idx, end_idx = st.select_slider(
                        "הזז את האצבע לבחירת טווח המדידה בגרף:",
                        options=range(len(time_list)),
                        value=(0, len(time_list)-1),
                        format_func=lambda x: time_list[x],
                        key="tech_slider"
                    )
                    
                    p1 = df_tech['Close'].iloc[start_idx]
                    p2 = df_tech['Close'].iloc[end_idx]
                    pct_diff = ((p2 - p1) / p1) * 100
                    price_diff = p2 - p1
                    
                    t1_val = df_tech.index[start_idx]
                    t2_val = df_tech.index[end_idx]

                    # הצגת נתוני המדידה מעל הגרף בריבועים מעוצבים
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("טווח שנמדד", f"{time_list[start_idx]} ➡️ {time_list[end_idx]}")
                    with col_m2:
                        color_arrow = "🔺" if price_diff >= 0 else "🔻"
                        st.metric("שינוי במחיר ($)", f"${price_diff:.2f}", f"{color_arrow} ${abs(price_diff):.2f}")
                    with col_m3:
                        if pct_diff >= 0:
                            st.markdown(f"<div style='background-color:#e6f4ea; padding:10px; border-radius:8px; text-align:center;'><span style='color:#137333; font-size:14px; font-weight:600;'>תשואה בטווח</span><br><b style='color:#137334; font-size:22px;'>+{pct_diff:.2f}%</b></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='background-color:#fce8e6; padding:10px; border-radius:8px; text-align:center;'><span style='color:#c5221f; font-size:14px; font-weight:600;'>תשואה בטווח</span><br><b style='color:#c5221f; font-size:22px;'>{pct_diff:.2f}%</b></div>", unsafe_allow_html=True)
                    
                    st.write("---")

                    # בניית הגרף ב-3 קומות מותאמות
                    fig_tech = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.55, 0.22, 0.23])
                    
                    # קומה 1: מחיר (נרות יפניים - תיקון הגדרת הציטוטים של ה-Line)
                    fig_tech.add_trace(go.Candlestick(
                        x=df_tech.index, open=df_tech['Open'], high=df_tech['High'], low=df_tech['Low'], close=df_tech['Close'],
                        name='מחיר',
                        increasing=dict(line=dict(color='#089981'), fillcolor='#089981'),
                        decreasing=dict(line=dict(color='#f23645'), fillcolor='#f23645')
                    ), row=1, col=1)
                    
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA_Fast'], mode='lines', name=fast_label, line=dict(color='#ff9f43', width=1.5)), row=1, col=1)
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA_Slow'], mode='lines', name=slow_label, line=dict(color='#2196f3', width=1.5)), row=1, col=1)
                    
                    # קומה 2: ווליום דינמי + הדגשת פריצות
                    colors = []
                    opacities = []
                    for _, row in df_tech.iterrows():
                        is_bullish = row['Close'] >= row['Open']
                        base_color = '#089981' if is_bullish else '#f23645'
                        colors.append(base_color)
                        
                        # הדגשת עמודות שעוברות את הממוצע הנע שלהן באותו זמן
                        if not pd.isna(row['Vol_MA_3M']) and row['Volume'] >= row['Vol_MA_3M']:
                            opacities.append(1.0)
                        else:
                            opacities.append(0.25)
                    
                    fig_tech.add_trace(go.Bar(
                        x=df_tech.index, y=df_tech['Volume'], name='ווליום',
                        marker=dict(color=colors, opacity=opacities), showlegend=False
                    ), row=2, col=1)
                    
                    # קו ממוצע ווליום נע ודינמי (כחול רציף, זז יחד עם הגרף)
                    fig_tech.add_trace(go.Scatter(
                        x=df_tech.index, y=df_tech['Vol_MA_3M'], mode='lines',
                        name=vol_label, line=dict(color='#2563eb', width=2)
                    ), row=2, col=1)
                    
                    # קומה 3: מתנד RSI
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['RSI'], mode='lines', name='RSI', line=dict(color='#7e57c2', width=1.5)), row=3, col=1)
                    fig_tech.add_shape(type="line", x0=df_tech.index[0], y0=70, x1=df_tech.index[-1], y1=70, line=dict(color="#f23645", width=1, dash="dash"), row=3, col=1)
                    fig_tech.add_shape(type="line", x0=df_tech.index[0], y0=30, x1=df_tech.index[-1], y1=30, line=dict(color="#089981", width=1, dash="dash"), row=3, col=1)
                    
                    # 🔥 פיצ'רTradingView בלעדי: הזרקת מלבן הצללה דינמי על פי בחירת הסליידר
                    fig_tech.add_vrect(
                        x0=t1_val, x1=t2_val,
                        fillcolor="#64748b", opacity=0.12,
                        layer="below", line_width=0,
                        row="all", col=1
                    )
                    
                    # הגדרות קרוסהייר אנכי ואופטימיזציה למובייל
                    fig_tech.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', spikethickness=1, spikedash='solid', spikecolor='#94a3b8')
                    fig_tech.update_layout(
                        hovermode='x unified', dragmode=False, xaxis_rangeslider_visible=False, height=650,
                        template="plotly_white", margin=dict(l=5, r=5, t=5, b=5),
                        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=10))
                    )
                    
                    st.plotly_chart(fig_tech, use_container_width=True, config={'scrollZoom': False, 'displayModeBar': False})
                    
        except Exception as e:
            st.error(f"אירעה שגיאה בעיבוד הנתונים: {e}")
