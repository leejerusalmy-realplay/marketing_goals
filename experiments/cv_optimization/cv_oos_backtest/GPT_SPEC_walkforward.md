*Lee Jerusalmy*

# GPT spec — walk-forward CV vs OOS goal error

Source prompt Lee used (GPT-assisted) to define experiment **`cv_oos_backtest`**.  
Implemented notebook: `Marketing_Goals_Combined_RP_LS_Colab.ipynb` in this folder.  
See also `NOTES.md` and parent `../EXPERIMENT_LOG.md`.

---

I want to create a new, separate experiment notebook based on the existing Marketing Goals methodology.

The previous experiments (Robust CV and High-CV Diagnosis) should remain untouched. Do not modify, interrupt, or overwrite them.

The purpose of this experiment is not to reduce CV.

The purpose is to answer a more important question:

Does a high CV actually mean that the Marketing Goal produced by the model is unreliable out-of-sample?

In particular, we observed that early patches such as 1->7 naturally have much higher CV than mature patches. Before changing the CV thresholds, I want to test whether those high-CV goals are actually less predictive of future cohorts.

Core experiment

Perform a historical rolling / walk-forward backtest of the existing Marketing Goals methodology.

The backtest must simulate what we would have known at each historical point in time.

There must be no look-ahead bias.

For each:

brand × population × patch

and for multiple historical cutoff dates:

1. Take only cohort dates that would have been available at that historical point.
2. Apply the existing Marketing Goals methodology exactly as it exists today, including:
    * cohort eligibility
    * 35-cohort lookback
    * existing trimming / winsorization
    * exclusions
    * CV calculation
    * existing goal calculation
    * any other existing relevant logic
3. Produce the Marketing Goal that the model would have generated at that point in time.
4. Freeze that goal.
5. Evaluate it against future cohort dates that were not used to calculate the goal.

The goal is to compare:

In-sample CV → Out-of-sample Goal Error

⸻

1. Do not change the existing model

This is critical.

Do not:

* change CV
* introduce Robust CV into the production calculation
* change trimming
* change the 35-cohort window
* introduce patch-specific thresholds
* optimize parameters
* change Marketing Goal formulas

This experiment should test the current methodology as-is.

If technical changes are required to make historical execution possible, isolate them to the backtesting framework and document them.

⸻

2. Walk-forward methodology

For each historical evaluation point:

Training window

Use the exact historical cohort window that the current methodology would have used.

For example:

35 eligible historical cohort dates

Apply all existing logic and calculate:

goal_at_time_t

and:

cv_after_at_time_t

Test window

Then evaluate the frozen goal against the next eligible cohort dates that were not included in training.

I want multiple test horizons if the data allows it.

At minimum try:

* next 7 cohort dates
* next 14 cohort dates
* next 30 cohort dates

If some combinations do not have enough future data, report that rather than artificially filling the test window.

⸻

3. Define out-of-sample error

For every future cohort observation, compare:

actual cohort metric

against:

goal predicted from historical training window

Calculate at least:

Absolute Error

abs(actual - goal)

Absolute Percentage Error

abs(actual - goal) / abs(goal)

Handle zero or near-zero goals safely.

Signed Error

actual - goal

This allows us to identify systematic over/under prediction.

Also calculate test-window aggregate metrics:

* MAE
* Median Absolute Error
* MAPE where mathematically appropriate
* Median Absolute Percentage Error
* RMSE
* Mean Signed Error / Bias

Do not rely on MAPE alone.

⸻

4. Most important analysis: CV vs future prediction error

For every historical training window, save:

brand
population
patch
training_start
training_end
n_training_cohorts
n_training_users
goal
cv_before
cv_after
flagged_using_existing_logic
test_horizon
n_test_cohorts
test_mae
test_median_ae
test_mape
test_median_ape
test_rmse
test_bias

Then analyze the relationship between:

cv_after and future prediction error

This is the central question of the notebook.

I want to know:

Does higher CV actually predict higher out-of-sample error?

Calculate correlations between CV and the different error measures.

Show both:

* Pearson correlation
* Spearman rank correlation

Do this overall and by patch.

⸻

5. Test the existing 15% threshold

The current methodology treats approximately:

CV > 0.15

as problematic in relevant cases.

I want to empirically test whether that threshold actually separates reliable from unreliable goals.

Compare historical backtests where:

Group A

CV <= 0.15

versus:

Group B

CV > 0.15

For both groups compare:

* median future error
* mean future error
* P75 error
* P90 error
* bias
* number of observations

Do this overall and by patch.

The question is:

Do goals with CV >15% actually perform materially worse out-of-sample?

Do not assume the answer is yes.

⸻

6. Patch-specific analysis

This is extremely important.

From the previous diagnosis experiment, we observed approximately:

* 1->7 has much higher natural CV
* later patches generally have substantially lower CV

Therefore analyze each patch separately:

1->7
7->14
14->30
30->60
60->90
90->120
120->150
150->180
180->270
270->365

For each patch show:

* median historical CV
* P75 CV
* P90 CV
* median out-of-sample error
* P75 out-of-sample error
* P90 out-of-sample error
* correlation between CV and error
* percentage of windows with CV >15%
* performance of CV <=15% vs CV >15%

I specifically want to know whether:

CV=20–25% may be normal and still predictive for 1->7, while the same CV would indicate a serious problem for a mature patch.

⸻

7. CV buckets

Create empirical CV buckets, for example:

< 5%
5–10%
10–15%
15–20%
20–25%
25–30%
>30%

For each bucket show:

* number of historical predictions
* median prediction error
* P75 prediction error
* P90 prediction error
* median bias

Do this overall and by patch where sample size allows.

The objective is to see whether prediction error actually increases as CV increases.

Do not force monotonicity.

If the relationship is weak or inconsistent, report that clearly.

⸻

8. Special focus on 1->7

The previous analysis strongly suggested that 1->7 has naturally higher CV.

Therefore create a dedicated section for 1->7.

For every historical backtest window show:

brand
population
training_end
goal
cv_after
next_7_error
next_14_error
next_30_error

Then answer empirically:

Question A

When 1->7 CV is between 15–20%, how accurate is the resulting goal?

Question B

When CV is between 20–25%, how accurate is it?

Question C

When CV is >25%, does prediction accuracy deteriorate materially?

Question D

Is there a meaningful CV level after which the goal becomes clearly unreliable?

Do not create a threshold unless the data provides evidence for one.

⸻

9. Population and sample-size effects

Break the analysis down by:

* Affiliate
* App
* Web
* Blended

and by brand.

Also examine whether the relationship:

CV → prediction error

changes depending on sample size.

For example, compare similar CV values where:

* user count is large
* user count is small

This is especially important for populations such as RealPrize Web, where some historical patches have relatively small user counts.

⸻

10. Goal stability over time

For each:

brand × population × patch

plot the historical Marketing Goal produced at each backtest date.

Show:

historical calculation date → Marketing Goal

and optionally overlay:

CV at that calculation date

I want to see whether the goal itself is stable over time.

A patch could have high cohort-level CV while the estimated Marketing Goal remains relatively stable across rolling windows.

That distinction is very important.

Calculate a simple measure of goal stability across historical backtest windows.

⸻

11. Visualizations

Create diagnostic visualizations including:

CV vs prediction error

Scatter plot:

CV after → out-of-sample error

Include the existing 15% CV threshold as a reference line.

CV vs error by patch

Create separate views for the major patches, especially:

* 1->7
* 7->14
* 14->30
* 30->60
* 60->90
* 90->120

Error by CV bucket

Show the distribution of out-of-sample errors for each CV bucket.

Rolling goal stability

Show Marketing Goal over historical calculation dates.

1->7 deep dive

Clearly visualize whether prediction error increases with CV for the early patch.

Keep plots diagnostic and readable.

⸻

12. Avoid look-ahead bias

This is the most important technical requirement.

At every historical backtest date:

The model may only use information that would have been available at that point in time.

Future cohorts must never affect:

* trimming
* cohort selection
* CV
* goal calculation
* exclusions
* thresholds
* any training statistic

If any part of the current pipeline accidentally uses future information, explicitly identify it.

⸻

13. Final decision table

At the end of the notebook, create a concise summary by patch:

patch
median_cv
p90_cv
median_oos_error
p90_oos_error
corr_cv_error_pearson
corr_cv_error_spearman
median_error_cv_le_15
median_error_cv_gt_15
n_backtests
interpretation

The interpretation should be descriptive, for example:

* "Higher CV strongly associated with worse future prediction"
* "Moderate relationship"
* "Weak relationship"
* "No meaningful relationship detected"
* "CV >15% does not materially reduce predictive accuracy"
* "Insufficient historical observations"

Do not automatically recommend a new threshold.

⸻

Final questions the notebook must answer

At the end, write a concise analysis answering:

1. Does CV actually predict future Marketing Goal error?

2. Does the current 15% threshold have empirical predictive value?

3. Is the relationship between CV and reliability different by patch?

4. Is high CV in 1->7 actually problematic, or is it mostly natural early-lifecycle variability?

5. Are there cases where CV is high but the Marketing Goal remains stable and predicts future cohorts well?

6. Are there cases where CV is low but the Marketing Goal still performs poorly out-of-sample?

7. Based only on this backtest, is there evidence that we should eventually use patch-specific CV expectations rather than one universal threshold?

Do not change the production methodology based on these results.

This experiment is intended to provide the empirical evidence needed before we decide whether to change the CV thresholds or stability methodology.
