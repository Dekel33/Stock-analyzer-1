import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# הגדרות עיצוב מתקדמות ומראה מקצועי
st.set_page_config(page_title="מערכת ניתוח מניות Pro", layout="wide", initial_sidebar_state="expanded")

# הזרקת קוד CSS מותאם אישית למראה נקי, מקצועי ותמיכה ביישור לימין (RTL) לחלקים בעברית
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [data-testid="stSidebarUserContent"] {
        font-family: 'Inter', sans-serif;
    }
    
    .rtl-container {
        direction: rtl;
        text-align: right;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        padding-right: 20px;
        padding-left: 20px;
    }
    
    .card-title {
        font-size: 14px;
        color: #888888;
        margin-bottom: 5px;
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
st.markdown("<div class='rtl-container'><h1>📈 מערכת פרימיום לניתוח ומעקב מניות</h1><p style='color:#666;'>אנליזה פנדמנטלית וטכנית מתקדמת בזמן אמת</p></div>", unsafe_allow_html=True)

# תיבת קלט מעוצבת
ticker = st.text_input("הכנס טיקר של מניה (למשל: PANW, NVDA, AAPL, MSFT):", "AAPL").upper().strip()

if ticker:
    with st.spinner('מחלץ נתונים פיננסיים ומחשב אינדיקטורים...'):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or 'longName' not in info:
                st.error(f"לא נמצאו נתונים עבור הטיקר: {ticker}. אנא ודא שהקשדת אותו נכון.")
                st.stop()
                
            financials = stock.financials         
            balance_sheet = stock.balance_sheet   
            cashflow = stock.cashflow             
            
            company_name = info.get('longName', ticker)
            sector = info.get('sector', 'לא ידוע')
            industry = info.get('industry', 'לא ידוע')
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            # תצוגת שורת סטטוס עליונה מקצועית
            st.markdown(f"""
                <div class='rtl-container' style='background-color:#f8f9fa; padding:15px; border-radius:8px; margin-bottom:20px; border: 1px solid #e9ecef;'>
                    <span style='font-size:20px; font-weight:700; color:#1e293b;'>{company_name} ({ticker})</span> | 
                    <span style='color:#64748b;'>סקטור:</span> <b>{sector}</b> | 
                    <span style='color:#64748b;'>תעשייה:</span> <b>{industry}</b> | 
                    <span style='color:#64748b;'>מחיר שוק:</span> <b style='color:#0f172a; font-size:18px;'>${current_price:.2f}</b>
                </div>
            """, unsafe_allow_html=True)
            
            # יצירת הטאבים
            tab1, tab2 = st.tabs(["🔍 אנליזה פנדמנטלית ותעודת זהות", "📊 חדר ניתוח טכני מקצועי"])
            
            # ==========================================
            # טאב 1: ניתוח פנדמנטלי + תעודת זהות
            # ==========================================
            with tab1:
                col_graph, col_id = st.columns([2, 1])
                
                with col_graph:
                    st.subheader("📊 ביצועי מניה היסטוריים מהירים")
                    timeframe_fund = st.radio(
                        "בחר טווח זמן:",
                        ["1D", "5D", "1M", "6M", "1Y", "YTD", "3Y", "5Y"],
                        index=4, key="fund_tf", horizontal=True
                    )
                    
                    tf_mapping_fund = {
                        "1D": {"period": "1d", "interval": "5m"},
                        "5D": {"period": "5d", "interval": "15m"},
                        "1M": {"period": "1mo", "interval": "1d"},
                        "6M": {"period": "6mo", "interval": "1d"},
                        "1Y": {"period": "1y", "interval": "1d"},
                        "YTD": {"period": "ytd", "interval": "1d"},
                        "3Y": {"period": "3y", "interval": "1d"},
                        "5Y": {"period": "5y", "interval": "1d"}
                    }
                    
                    opts_f = tf_mapping_fund[timeframe_fund]
                    df_fund_chart = stock.history(period=opts_f["period"], interval=opts_f["interval"])
                    
                    if not df_fund_chart.empty:
                        fig_fund = go.Figure()
                        fig_fund.add_trace(go.Scatter(x=df_fund_chart.index, y=df_fund_chart['Close'], mode='lines', name='מחיר', line=dict(color='#0f172a', width=2)))
                        
                        # הגדרות סמן אחיד לגרף הפנדמנטלי למניעת זום מקרי
                        fig_fund.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', spikethickness=1, spikedash='dash', spikecolor='#888888')
                        fig_fund.update_layout(
                            hovermode='x unified', 
                            dragmode=False, 
                            height=380, 
                            template="plotly_white",
                            margin=dict(l=10, r=10, t=10, b=10)
                        )
                        st.plotly_chart(fig_fund, use_container_width=True, config={'scrollZoom': False, 'displayModeBar': False})
                
                with col_id:
                    st.markdown("<div class='rtl-container'><h3>🪪 פרופיל ותעודת זהות למניה</h3></div>", unsafe_allow_html=True)
                    
                    # חילוץ פרמטרים לתעודת הזהות
                    market_cap = info.get('marketCap')
                    operating_cf = info.get('operatingCashflow')
                    p_cf = (market_cap / operating_cf) if market_cap and operating_cf else info.get('priceToCashFlow')
                    pe = info.get('trailingPE')
                    fwd_pe = info.get('forwardPE')
                    peg = info.get('pegRatio')
                    fwd_peg = info.get('forwardPegRatio', "N/A")
                    
                    earnings_yield = (1 / pe) * 100 if pe else None
                    cf_yield = (operating_cf / market_cap) * 100 if operating_cf and market_cap else None
                    free_cash_flow = info.get('freeCashflow')
                    fcf_yield = (free_cash_flow / market_cap) * 100 if free_cash_flow and market_cap else None
                    div_yield = info.get('dividendYield')
                    payout_ratio = info.get('payoutRatio')
                    
                    total_cash = info.get('totalCash')
                    total_debt = info.get('totalDebt')
                    net_balance = (total_cash - total_debt) if total_cash is not None and total_debt is not None else None
                    
                    gross_margin = info.get('grossMargins')
                    operating_margin = info.get('operatingMargins')
                    net_margin = info.get('profitMargins')
                    
                    with st.container(border=True):
                        st.markdown("**💰 Financials**")
                        st.write(f"**Market Cap:** {format_large_num(market_cap)}")
                        st.write(f"**P/CF:** {f'{p_cf:.2f}' if p_cf else 'N/A'}")
                        st.write(f"**PE / FWD PE:** {f'{pe:.2f}' if pe else 'N/A'} / {f'{fwd_pe:.2f}' if fwd_pe else 'N/A'}")
                        st.write(f"**PEG / FWD PEG:** {f'{peg:.2f}' if peg else 'N/A'} / {f'{fwd_peg:.2f}' if isinstance(fwd_peg, float) else fwd_peg}")
                        st.markdown("---")
                        st.markdown("**📈 Yields**")
                        st.write(f"**Earnings Yield (TTM):** {f'{earnings_yield:.2f}%' if earnings_yield else 'N/A'}")
                        st.write(f"**C/F Yield (TTM):** {f'{cf_yield:.2f}%' if cf_yield else 'N/A'}")
                        st.write(f"**FCF Yield (TTM):** {f'{fcf_yield:.2f}%' if fcf_yield else 'N/A'}")
                        st.write(f"**Dividend Yield (TTM):** {format_pct(div_yield)}")
                        st.write(f"**Payout Ratio (TTM):** {format_pct(payout_ratio)}")
                        st.markdown("---")
                        st.markdown("**⚖️ Balances**")
                        st.write(f"**Total Cash (MRQ):** {format_large_num(total_cash)}")
                        st.write(f"**Total Debt:** {format_large_num(total_debt)}")
                        if net_balance and net_balance > 0:
                            st.markdown(f"**Net:** <span style='color:#16a34a; font-weight:600;'>{format_large_num(net_balance)} (עודף מזומן)</span>", unsafe_allow_html=True)
                        elif net_balance:
                            st.markdown(f"**Net:** <span style='color:#dc2626; font-weight:600;'>{format_large_num(net_balance)} (חוב נטו)</span>", unsafe_allow_html=True)
                        st.markdown("---")
                        st.markdown("**📊 Margins**")
                        st.write(f"**Gross Profit Margin:** {format_pct(gross_margin)}")
                        st.write(f"**Operating Margin:** {format_pct(operating_margin)}")
                        st.write(f"**Net Income Margin:** {format_pct(net_margin)}")

                st.write("---")
                st.markdown("<div class='rtl-container'><h3>📋 כרטיס ניקוד וחוקי סינון חכמים</h3></div>", unsafe_allow_html=True)
                roe = info.get('returnOnEquity')
                rev_growth = info.get('revenueGrowth')
                earnings_growth = info.get('earningsGrowth')
                current_ratio = info.get('currentRatio')
                debt_to_equity = info.get('debtToEquity')
                
                col_sc1, col_sc2 = st.columns(2)
                with col_sc1:
                    roe_text = f"{roe*100:.1f}%" if roe else "N/A"
                    if roe and roe >= 0.15: st.success(f"✅ **תשואה על ההון (ROE):** {roe_text} (עומד ביעד של מעל 15%)")
                    else: st.error(f"❌ **תשואה על ההון (ROE):** {roe_text} (מתחת ליעד של 15%)")
                    if rev_growth and rev_growth > 0: st.success(f"✅ **צמיחת הכנסות חיובית:** {rev_growth*100:.1f}%")
                    else: st.error(f"❌ **אין צמיחת הכנסות או שהיא שלילית:** {f'{rev_growth*100:.1f}%' if rev_growth else 'N/A'}")
                    if earnings_growth and rev_growth:
                        if earnings_growth > rev_growth: st.success(f"✅ **צמיחת ה-EPS מהירה מההכנסות:** {earnings_growth*100:.1f}% מול {rev_growth*100:.1f}%")
                        else: st.warning(f"⚠️ **צמיחת ה-EPS איטית מקצב צמיחת ההכנסות.**")
                
                with col_sc2:
                    if current_ratio and current_ratio >= 1: st.success(f"✅ **יחס שוטף:** {current_ratio:.2f} (גדול מ-1, נזילות בריאה)")
                    else: st.error(f"❌ **יחס שוטף:** {current_ratio if current_ratio else 'N/A'} (סיכון נזילות לטווח קצר)")
                    if debt_to_equity:
                        leverage = debt_to_equity / 100
                        if leverage <= 1: st.success(f"✅ **מנוף פיננסי (חוב להון):** {leverage:.2f} (בריא ומאוזן)")
                        else: st.error(f"❌ **מנוף פיננסי (חוב להון):** {leverage:.2f} (גבוה מדי)")
                    if operating_cf and free_cash_flow:
                        fcf_to_ocf_ratio = free_cash_flow / operating_cf
                        growth_sectors = ['Technology', 'Technology Hardware', 'Semiconductors', 'Energy', 'Clean Energy']
                        is_growth_sector = any(sec.lower() in sector.lower() for sec in growth_sectors)
                        if fcf_to_ocf_ratio >= 0.50: st.success(f"✅ **תזרים חופשי מעולה:** {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל")
                        else:
                            if is_growth_sector: st.warning(f"⚠️ **תזרים חופשי מהווה {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל.** חברת סקטור {sector} - השקעות גבוהות (CapEx) נפוצות בשלב זה.")
                            else: st.error(f"❌ **תזרים חופשי נמוך:** {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל")

            # ==========================================
            # טאב 2: ניתוח טכני מתקדם (נעילת זום, סמן קרוסהייר וממוצע נפח 3M)
            # ==========================================
            with tab2:
                st.markdown("<div class='rtl-container'><h3>📉 חדר ניתוח טכני ואינדיקטורים</h3></div>", unsafe_allow_html=True)
                
                timeframe_tech = st.radio(
                    "בחר טווח זמן לניתוח טכני:",
                    ["1D", "5D", "1M", "6M", "1Y", "YTD", "3Y", "5Y"],
                    index=4, key="tech_tf", horizontal=True
                )
                
                is_intraday = timeframe_tech in ["1D", "5D"]
                
                if is_intraday:
                    interval = "5m" if timeframe_tech == "1D" else "15m"
                    df_tech = stock.history(period=timeframe_tech.lower(), interval=interval)
                    
                    if not df_tech.empty:
                        df_tech['MA_Fast'] = df_tech['Close'].ewm(span=9, adjust=False).mean()
                        df_tech['MA_Slow'] = df_tech['Close'].ewm(span=21, adjust=False).mean()
                        df_tech['RSI'] = calculate_rsi(df_tech['Close'], period=14)
                        # לתוך היום נשמור את ממוצע הנפח הקצר
                        df_tech['Vol_SMA'] = df_tech['Volume'].rolling(window=20).mean()
                        # נשלוף את ממוצע ה-3 חודשים היומי הכללי כקו ייחוס קבוע
                        df_daily_ref = stock.history(period="3mo", interval="1d")
                        avg_3m_val = df_daily_ref['Volume'].mean() if not df_daily_ref.empty else 0
                        df_tech['Vol_MA_3M'] = avg_3m_val
                        
                        fast_label, slow_label = "EMA 9 (מהיר)", "EMA 21 (איטי)"
                        vol_3m_label = "ממוצע נפח יומי 3 חודשים (קו קבוע)"
                else:
                    # פתרון חיתוך חכם - מושכים תמיד 5 שנים לחישוב ממוצעים מלאים
                    df_full = stock.history(period="5y", interval="1d")
                    
                    if not df_full.empty:
                        df_full['MA_Fast'] = df_full['Close'].rolling(window=50).mean()
                        df_full['MA_Slow'] = df_full['Close'].rolling(window=150).mean()
                        df_full['RSI'] = calculate_rsi(df_full['Close'], period=14)
                        
                        # שדרוג: חישוב ממוצע נפח מסחר ל-3 חודשים אחרונים (63 ימי מסחר)
                        df_full['Vol_MA_3M'] = df_full['Volume'].rolling(window=63).mean()
                        df_full['Vol_SMA'] = df_full['Volume'].rolling(window=20).mean()
                        
                        fast_label, slow_label = "SMA 50", "SMA 150"
                        vol_3m_label = "ממוצע נפח 3 חודשים (SMA 63)"
                        
                        last_date = df_full.index[-1]
                        if timeframe_tech == "1M": start_date = last_date - pd.Timedelta(days=30)
                        elif timeframe_tech == "6M": start_date = last_date - pd.Timedelta(days=182)
                        elif timeframe_tech == "1Y": start_date = last_date - pd.Timedelta(days=365)
                        elif timeframe_tech == "YTD": start_date = pd.Timestamp(year=last_date.year, month=1, day=1, tz=last_date.tz)
                        elif timeframe_tech == "3Y": start_date = last_date - pd.Timedelta(days=365*3)
                        else: start_date = df_full.index[0]
                            
                        df_tech = df_full.loc[start_date:]
                    else:
                        df_tech = pd.DataFrame()
                
                if df_tech.empty:
                    st.error("לא ניתן היה למשוך נתוני מחיר עבור טווח הזמן שנבחר.")
                else:
                    # מנוע זיהוי פריצה אוטומטי
                    last_vol = df_tech['Volume'].iloc[-1]
                    last_vol_3m = df_tech['Vol_MA_3M'].iloc[-1]
                    
                    if not pd.isna(last_vol_3m) and last_vol_3m > 0:
                        vol_ratio = last_vol / last_vol_3m
                        if vol_ratio >= 1.5:
                            price_change = df_tech['Close'].iloc[-1] - df_tech['Open'].iloc[-1]
                            st.markdown("<div class='rtl-container'><h4>🔔 איתות פריצת מחזור מסחר</h4></div>", unsafe_allow_html=True)
                            if price_change > 0:
                                st.success(f"🔥 **פריצה שורית!** המניה נסחרת בנפח חריג הגבוה פי **{vol_ratio:.1f}** מממוצע ה-3 חודשים שלה בליווי עליות מחיר.")
                            else:
                                st.error(f"⚠️ **לחץ מוכרים/שבירה!** נפח חריג גבוה פי **{vol_ratio:.1f}** מממוצע ה-3 חודשים מלווה בירידות שערים.")
                            st.write("---")

                    # בניית 3 קומות נפרדות לגרפים
                    fig_tech = make_subplots(
                        rows=3, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.02,
                        row_heights=[0.55, 0.20, 0.25]
                    )
                    
                    # קומה 1: מחיר המניה (נרות וממוצעים)
                    fig_tech.add_trace(go.Candlestick(
                        x=df_tech.index, open=df_tech['Open'], high=df_tech['High'],
                        low=df_tech['Low'], close=df_tech['Close'], name='מחיר'
                    ), row=1, col=1)
                    
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA_Fast'], mode='lines', name=fast_label, line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA_Slow'], mode='lines', name=slow_label, line=dict(color='#3b82f6', width=1.5)), row=1, col=1)
                    
                    # קומה 2: ווליום + ממוצע 3 חודשים החדש!
                    colors = ['#10b981' if row['Close'] >= row['Open'] else '#ef4444' for _, row in df_tech.iterrows()]
                    fig_tech.add_trace(go.Bar(
                        x=df_tech.index, y=df_tech['Volume'], name='נפח מסחר',
                        marker_color=colors, opacity=0.5, showlegend=False
                    ), row=2, col=1)
                    
                    # קו ממוצע נפח 3 חודשים
                    fig_tech.add_trace(go.Scatter(
                        x=df_tech.index, y=df_tech['Vol_MA_3M'], mode='lines', 
                        name=vol_3m_label, line=dict(color='#dc2626', width=2, dash='solid')
                    ), row=2, col=1)
                    
                    # קומה 3: מתנד RSI
                    fig_tech.add_trace(go.Scatter(
                        x=df_tech.index, y=df_tech['RSI'], mode='lines', name='RSI (14)',
                        line=dict(color='#8b5cf6', width=1.5)
                    ), row=3, col=1)
                    
                    fig_tech.add_shape(type="line", x0=df_tech.index[0], y0=70, x1=df_tech.index[-1], y1=70, line=dict(color="#ef4444", width=1, dash="dash"), row=3, col=1)
                    fig_tech.add_shape(type="line", x0=df_tech.index[0], y0=30, x1=df_tech.index[-1], y1=30, line=dict(color="#10b981", width=1, dash="dash"), row=3, col=1)
                    
                    # --- הפיצ'ר החשוב ביותר: נעילת זום והגדרת קרוסהייר אנכי אחיד לנייד ומחשב ---
                    fig_tech.update_xaxes(
                        showspikes=True, 
                        spikemode='across', # קו רציף שעובר דרך כל הקומות במקביל
                        spikesnap='cursor', 
                        spikethickness=1, 
                        spikedash='dash', 
                        spikecolor='#64748b'
                    )
                    
                    fig_tech.update_layout(
                        hovermode='x unified', # חלונית מידע אחת מאוחדת וברורה לכל הקווים בנקודת הזמן
                        dragmode=False,        # מונע לחלוטין גרירה ושינוי זום מעצבן בנגיעה (מחשב/נייד)
                        height=800,
                        template="plotly_white",
                        margin=dict(l=10, r=10, t=30, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1)
                    )
                    
                    # הצגת הגרף וביטול כפתורי הזום מסרגל הכלים העליון של פלוטלי לנוחות מקסימלית
                    st.plotly_chart(
                        fig_tech, 
                        use_container_width=True, 
                        config={
                            'scrollZoom': False, 
                            'displayModeBar': True,
                            'modeBarButtonsToRemove': ['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut', 'autoScale', 'resetScale', 'toggleHover']
                        }
                    )
                    
                    last_rsi = df_tech['RSI'].iloc[-1]
                    if not pd.isna(last_rsi):
                        st.write(f"**מדד RSI נוכחי:** {last_rsi:.2f}")
                        if last_rsi >= 70: st.markdown("<span style='color:#dc2626;'>⚠️ קניית יתר (Overbought)</span>", unsafe_allow_html=True)
                        elif last_rsi <= 30: st.markdown("<span style='color:#16a34a;'>✅ מכירת יתר (Oversold)</span>", unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"אירעה שגיאה בעיבוד הנתונים: {e}")
