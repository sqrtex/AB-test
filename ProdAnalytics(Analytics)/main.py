import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.stats.proportion import proportions_ztest
# Уважаемый проверяющий, не забудьте скачать библиотеки для успешной проверки скрипта

file_path = 'dannye-dlia-keisa-po-pa-cebbefc3-5b29-4f88-b6d4-3336c88d743f.xlsx'
users = pd.read_excel(file_path, sheet_name='Пользователи')
payments = pd.read_excel(file_path, sheet_name='Платежи')

users_clean = users[(users['age'] >= 18) & (users['age'] <= 100)].copy()
users_clean = users_clean.dropna(subset=['group', 'user_id'])
users_clean['user_id'] = users_clean['user_id'].astype(int)

payments_clean = payments.dropna(subset=['user_id']).copy()
payments_clean['user_id'] = payments_clean['user_id'].astype(int)

df = payments_clean.merge(users_clean[['user_id', 'group']], on='user_id', how='inner', suffixes=('_pay', '_user'))
df['group'] = df['group_user']
df = df[df['step1_opened'].notna()]

metrics = df.groupby('group').agg(
    total_step1=('payment_id', 'count'),
    success_step4=('step4_success', 'count')
).reset_index()
metrics['conversion_rate'] = metrics['success_step4'] / metrics['total_step1'] * 100


print("Метрики по группам:")
print(metrics)

successes = metrics['success_step4'].values
trials = metrics['total_step1'].values

stat, pval = proportions_ztest(count=successes, nobs=trials)
print(f"\nZ-statistic: {stat:.4f}")
print(f"P-value: {pval:.4f}")
if pval < 0.05:
    print("Результат: Разница статистически значима (p < 0.05).")
else:
    print("Результат: Разница статистически НЕ значима (p >= 0.05).")

funnel_data = pd.DataFrame({
    'Шаг': ['1. Открыл форму', '2. Ввел реквизиты', '3. Подтвердил', '4. Успешная оплата'],
    'A': [df[df['group']=='A']['step1_opened'].count(),
          df[df['group']=='A']['step2_entered'].count(),
          df[df['group']=='A']['step3_confirmed'].count(),
          df[df['group']=='A']['step4_success'].count()],
    'B': [df[df['group']=='B']['step1_opened'].count(),
          df[df['group']=='B']['step2_entered'].count(),
          df[df['group']=='B']['step3_confirmed'].count(),
          df[df['group']=='B']['step4_success'].count()]
})
funnel_data['A_pct'] = funnel_data['A'] / funnel_data['A'].iloc[0] * 100
funnel_data['B_pct'] = funnel_data['B'] / funnel_data['B'].iloc[0] * 100

fig, axes = plt.subplots(1, 2, figsize=(15, 6))


sns.barplot(data=metrics, x='group', y='conversion_rate', hue='group', palette=['#1f77b4', '#ff7f0e'], legend=False, ax=axes[0])
axes[0].set_title('Общая конверсия (Шаг 1 → Шаг 4)')
axes[0].set_ylabel('Конверсия (%)')
axes[0].set_xlabel('Группа')
for i, v in enumerate(metrics['conversion_rate']):
    axes[0].text(i, v + 1, f"{v:.1f}%", ha='center', fontweight='bold')

x = np.arange(len(funnel_data['Шаг']))
width = 0.35
axes[1].bar(x - width/2, funnel_data['A_pct'], width, label='Группа A', color='#1f77b4')
axes[1].bar(x + width/2, funnel_data['B_pct'], width, label='Группа B', color='#ff7f0e')
axes[1].set_ylabel('Процент от Шага 1 (%)')
axes[1].set_title('Воронка платежей ЖКХ')
axes[1].set_xticks(x)
axes[1].set_xticklabels(funnel_data['Шаг'], rotation=15)
axes[1].legend()

print("\nДанные для графика воронки:")
print(funnel_data[['Шаг', 'A_pct', 'B_pct']])

plt.tight_layout()
plt.show()
