import io
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title='TransactionGuard', page_icon='🛡️', layout='wide')
st.title('🛡️ TransactionGuard')
st.caption('An educational rule-based suspicious transaction detector — not a bank-grade fraud model.')

REQUIRED = ['transaction_id', 'timestamp', 'account_id', 'amount', 'merchant']
SAMPLE_PATH = Path(__file__).parent / 'sample_transactions.csv'

@st.cache_data
def sample_data():
    return pd.read_csv(SAMPLE_PATH)

with st.sidebar:
    st.header('Detection settings')
    high_amount = st.number_input('High-amount threshold (₹)', min_value=1, value=10000, step=500)
    rapid_count = st.slider('Transactions triggering rapid-activity flag', 2, 10, 3)
    rapid_minutes = st.slider('Rapid-activity time window (minutes)', 1, 120, 10)
    st.info('Rules are illustrative. A flag does not mean fraud occurred.')

uploaded = st.file_uploader('Upload a transaction CSV (or use the included example)', type=['csv'])
if uploaded:
    try:
        source = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f'Unable to read CSV: {exc}')
        st.stop()
else:
    source = sample_data()
    st.info('Showing synthetic demonstration data. Upload a CSV to analyze your own test transactions.')

missing = [col for col in REQUIRED if col not in source.columns]
if missing:
    st.error(f'Missing required column(s): {", ".join(missing)}. Required: {", ".join(REQUIRED)}')
    st.stop()

df = source.copy()
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
if df['timestamp'].isna().any() or df['amount'].isna().any() or (df['amount'] < 0).any():
    st.error('All timestamps must be valid and amounts must be nonnegative numbers.')
    st.stop()
if df['transaction_id'].isna().any() or df['account_id'].isna().any():
    st.error('Transaction IDs and account IDs cannot be empty.')
    st.stop()

df['high_amount_flag'] = df['amount'] >= high_amount
# Every transaction in a rapid cluster is flagged when >= threshold occur within the window.
df['rapid_activity_flag'] = False
ordered = df.sort_values(['account_id', 'timestamp']).copy()
for _, group in ordered.groupby('account_id', sort=False):
    timestamps = group['timestamp'].tolist()
    indices = group.index.tolist()
    left = 0
    flagged_positions = set()
    for right, time_right in enumerate(timestamps):
        while time_right - timestamps[left] > pd.Timedelta(minutes=rapid_minutes):
            left += 1
        if right - left + 1 >= rapid_count:
            flagged_positions.update(range(left, right + 1))
    if flagged_positions:
        df.loc[[indices[i] for i in flagged_positions], 'rapid_activity_flag'] = True

df['risk_score'] = df['high_amount_flag'].astype(int) * 50 + df['rapid_activity_flag'].astype(int) * 50
df['risk_level'] = df['risk_score'].map({0: 'Low', 50: 'Review', 100: 'High'})
df['reasons'] = df.apply(lambda r: ', '.join(label for flag, label in [
    ('high_amount_flag', 'Large amount'), ('rapid_activity_flag', 'Rapid activity')
] if r[flag]) or 'No rule triggered', axis=1)

flagged = df[df['risk_score'] > 0].copy()
a, b, c = st.columns(3)
a.metric('Transactions', len(df))
b.metric('Flagged for review', len(flagged))
c.metric('Flag rate', f'{len(flagged)/len(df):.1%}' if len(df) else '0%')

st.subheader('Transactions for review')
st.dataframe(flagged[['transaction_id', 'timestamp', 'account_id', 'amount', 'merchant', 'risk_level', 'reasons']], use_container_width=True)
if flagged.empty:
    st.success('No transactions match the selected rules.')

st.subheader('Risk level distribution')
counts = df['risk_level'].value_counts().reindex(['Low', 'Review', 'High'], fill_value=0)
st.bar_chart(counts)

st.subheader('All analyzed transactions')
st.dataframe(df[['transaction_id', 'timestamp', 'account_id', 'amount', 'merchant', 'risk_score', 'risk_level', 'reasons']], use_container_width=True)
st.download_button('Download full results (CSV)', data=df.to_csv(index=False).encode('utf-8'), file_name='transactionguard_results.csv', mime='text/csv')
st.download_button('Download flagged transactions (CSV)', data=flagged.to_csv(index=False).encode('utf-8'), file_name='transactionguard_flagged.csv', mime='text/csv')
