import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# הגדרות עיצוב בסיסיות בעברית ויישור לימין
st.set_page_config(page_title="מערכת ניתוח מניות חכמה", layout="wide", initial_sidebar_state="expanded")

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

# פונקציה לחישוב מתנד RSI מבוסס פנדס
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# כותרת ראשית
st.title("📊 מערכת לבחינת מניות בשוק ההון - גרסת פרו")

# תיבת קלט להזנת הטיקר
ticker = st.text_input("הכנס טיקר של מניה (למשל: AAPL, MSFT, NVDA):", "AAPL").upper().strip()

if ticker:
    with st.spinner('מושך נתונים מ-Yahoo Finance... אנא המתן'):
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
            
            st.subheader(f"חברה: {company_name} | סקטור: {sector} ({industry}) | מחיר נוכחי: ${current_price:.2f}")
            
            tab1, tab2 = st.tabs(["🔍 ניתוח פנדמנטלי + תעודת זהות", "📈 ניתוח טכני מתקדם"])
            
            # ==========================================
            # טאב 1: ניתוח פנדמנטלי + גרף מהיר ותעודת זהות
            # ==========================================
            with tab1:
                col_graph, col_id = st.columns([2, 1])
                
                with col_graph:
                    st.subheader("📈 גרף ביצועי מניה מהיר")
                    timeframe_fund = st.radio(
                        "בחר טווח זמן לגרף מהיר:",
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
                        fig_fund.add_trace(go.Scatter(x=df_fund_chart.index, y=df_fund_chart['Close'], mode='lines', name='מחיר סגירה', line=dict(color='#2ca02c', width=2)))
                        fig_fund.update_layout(title=f"גרף מניית {ticker} - טווח {timeframe_fund}", xaxis_title="תאריך/זמן", yaxis_title="מחיר ($)", height=400, template="plotly_white")
                        st.plotly_chart(fig_fund, use_container_width=True)
                
                with col_id:
                    st.markdown("<h3 style='text-align: right;'>🪪 תעודת זהות למניה</h3>", unsafe_allow_html=True)
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
                            st.markdown(f"**Net:** <span style='color:green;'>{format_large_num(net_balance)} (עודף מזומן)</span>", unsafe_allow_html=True)
                        elif net_balance:
                            st.markdown(f"**Net:** <span style='color:red;'>{format_large_num(net_balance)} (חוב נטו)</span>", unsafe_allow_html=True)
                        else:
                            st.write("**Net:** N/A")
                        st.markdown("---")
                        st.markdown("**📊 Margins**")
                        st.write(f"**Gross Profit Margin:** {format_pct(gross_margin)}")
                        st.write(f"**Operating Margin:** {format_pct(operating_margin)}")
                        st.write(f"**Net Income Margin:** {format_pct(net_margin)}")

                st.write("---")
                st.subheader("📋 כרטיס ניקוד וחוקים אוטומטיים")
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
                    if current_ratio and current_ratio >= 1: st.success(f"✅ **יחס שוטף:** {current_ratio:.2f} (גדול מ-1, נזילות טובה)")
                    else: st.error(f"❌ **יחס שוטף:** {current_ratio if current_ratio else 'N/A'} (סיכון נזילות)")
                    if debt_to_equity:
                        leverage = debt_to_equity / 100
                        if leverage <= 1: st.success(f"✅ **מנוף פיננסי (חוב להון):** {leverage:.2f} (בריא)")
                        else: st.error(f"❌ **מנוף פיננסי (חוב להון):** {leverage:.2f} (גבוה)")
                    if operating_cf and free_cash_flow:
                        fcf_to_ocf_ratio = free_cash_flow / operating_cf
                        growth_sectors = ['Technology', 'Technology Hardware', 'Semiconductors', 'Energy', 'Clean Energy']
                        is_growth_sector = any(sec.lower() in sector.lower() for sec in growth_sectors)
                        if fcf_to_ocf_ratio >= 0.50: st.success(f"✅ **תזרים חופשי מעולה:** {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל")
                        else:
                            if is_growth_sector: st.warning(f"⚠️ **תזרים חופשי מהווה {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל.** חברת סקטור {sector} - השקעות גבוהות (CapEx) לצורך צמיחה.")
                            else: st.error(f"❌ **תזרים חופשי נמוך:** {fcf_to_ocf_ratio*100:.1f}% מהתזרים המפעיל")

            # ==========================================
            # טאב 2: ניתוח טכני מתקדם + סורק פריצות נפח חכם
            # ==========================================
            with tab2:
                st.header(f"📉 חדר ניתוח טכני מקצועי - {ticker}")
                
                timeframe_tech = st.radio(
                    "בחר טווח זמן לגרף הטכני:",
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
                        # חישוב ממוצע נע של נפח מסחר לתוך היום
                        df_tech['Vol_SMA20'] = df_tech['Volume'].rolling(window=20).mean()
                        fast_label, slow_label = "EMA 9 (מהיר)", "EMA 21 (איטי)"
                else:
                    df_full = stock.history(period="5y", interval="1d")
                    
                    if not df_full.empty:
                        df_full['MA_Fast'] = df_full['Close'].rolling(window=50).mean()
                        df_full['MA_Slow'] = df_full['Close'].rolling(window=150).mean()
                        df_full['RSI'] = calculate_rsi(df_full['Close'], period=14)
                        # חישוב ממוצע נע של נפח המסחר בגרף יומי (20 יום)
                        df_full['Vol_SMA20'] = df_full['Volume'].rolling(window=20).mean()
                        fast_label, slow_label = "SMA 50 (טווח בינוני)", "SMA 150 (טווח ארוך)"
                        
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
                    # --- מנוע זיהוי פריצה אוטומטי ---
                    last_vol = df_tech['Volume'].iloc[-1]
                    last_vol_sma = df_tech['Vol_SMA20'].iloc[-1]
                    
                    # הצגת התראת פריצה בראש הטאב במידה ויש חריגה
                    if not pd.isna(last_vol_sma) and last_vol_sma > 0:
                        vol_ratio = last_vol / last_vol_sma
                        if vol_ratio >= 2.0: # פריצת נפח מוגדרת כפי 2 ומעלה מהממוצע
                            price_change = df_tech['Close'].iloc[-1] - df_tech['Open'].iloc[-1]
                            
                            st.markdown("### 🔔 מערכת זיהוי פריצות חכמה")
                            if price_change > 0:
                                st.success(f"🔥 **זיהוי פריצה שורית (Bullish Breakout)!** מניית {ticker} עולה בנפח מסחר חריג הגבוה פי **{vol_ratio:.1f}** מהממוצע של 20 התקופות האחרונות. כסף חכם נכנס למניה!")
                            else:
                                st.error(f"⚠️ **זיהוי לחץ מכירות כבד / שבירה (Bearish Breakdown)!** נפח המסחר גבוה פי **{vol_ratio:.1f}** מהממוצע, אך מלווה בירידות שערים. מוסדיים עשויים להפיץ סחורה החוצה.")
                            st.write("---")

                    # בניית הגרף ב-3 קומות
                    fig_tech = make_subplots(
                        rows=3, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03,
                        row_heights=[0.55, 0.20, 0.25]
                    )
                    
                    # קומה 1: נרות וממוצעים
                    fig_tech.add_trace(go.Candlestick(
                        x=df_tech.index, open=df_tech['Open'], high=df_tech['High'],
                        low=df_tech['Low'], close=df_tech['Close'], name='מחיר'
                    ), row=1, col=1)
                    
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA_Fast'], mode='lines', name=fast_label, line=dict(color='orange', width=1.5)), row=1, col=1)
                    fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MA_Slow'], mode='lines', name=slow_label, line=dict(color='blue', width=1.5)), row=1, col=1)
                    
                    # קומה 2: נפח מסחר + קו ממוצע נע לנפח (חדש!)
                    colors = ['green' if row['Close'] >= row['Open'] else 'red' for _, row in df_tech.iterrows()]
                    fig_tech.add_trace(go.Bar(
                        x=df_tech.index, y=df_tech['Volume'], name='נפח מסחר',
                        marker_color=colors, opacity=0.6, showlegend=True
                    ), row=2, col=1)
                    
                    # הוספת קו ממוצע נפח מעל העמודות
                    fig_tech.add_trace(go.Scatter(
                        x=df_tech.index, y=df_tech['Vol_SMA20'], mode='lines', 
                        name='ממוצע נפח (20)', line=dict(color='black', width=1.5, dash='dot')
                    ), row=2, col=1)
                    
                    # קומה 3: RSI
                    fig_tech.add_trace(go.Scatter(
                        x=df_tech.index, y=df_tech['RSI'], mode='lines', name='RSI (14)',
                        line=dict(color='purple', width=1.5)
                    ), row=3, col=1)
                    
                    fig_tech.add_shape(type="line", x0=df_tech.index[0], y0=70, x1=df_tech.index[-1], y1=70, line=dict(color="red", width=1, dash="dash"), row=3, col=1)
                    fig_tech.add_shape(type="line", x0=df_tech.index[0], y0=30, x1=df_tech.index[-1], y1=30, line=dict(color="green", width=1, dash="dash"), row=3, col=1)
                    
                    fig_tech.update_layout(
                        title=f"ניתוח טכני מתקדם עבור {ticker} (טווח נבחר: {timeframe_tech})",
                        yaxis_title="מחיר מניה ($)",
                        yaxis2_title="נפח מסחר",
                        yaxis3_title="RSI (0-100)",
                        xaxis_rangeslider_visible=False, 
                        height=800,
                        template="plotly_white",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    
                    st.plotly_chart(fig_tech, use_container_width=True)
                    
                    last_rsi = df_tech['RSI'].iloc[-1]
                    if not pd.isna(last_rsi):
                        st.write(f"**מדד RSI נוכחי:** {last_rsi:.2f}")
                        if last_rsi >= 70: st.markdown("<span style='color:red;'>⚠️ אזהרה: המניה נמצאת באזור קניית יתר (Overbought) - ייתכן מימוש קרוב.</span>", unsafe_allow_html=True)
                        elif last_rsi <= 30: st.markdown("<span style='color:green;'>✅ איתות: המניה נמצאת באזור מכירת יתר (Oversold) - ייתכן פוטנציאל להיפוך לעליות.</span>", unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"אירעה שגיאה בעיבוד הנתונים: {e}")
