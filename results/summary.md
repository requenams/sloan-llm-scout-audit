# Audit results

Valid responses: 9,402

## Consistency (baseline repeats)

| model    |   profiles |   repeats_mean |   icc_rating |   rating_within_sd |   share_rating_range_ge2 |   value_cv_mean |   value_ratio_max_min_median |   recommendation_stable_share |
|:---------|-----------:|---------------:|-------------:|-------------------:|-------------------------:|----------------:|-----------------------------:|------------------------------:|
| claude   |        147 |          5     |        0.978 |              0.054 |                    0     |           0.054 |                        1     |                         0.925 |
| deepseek |        147 |          4.993 |        0.842 |              0.305 |                    0.082 |           0.239 |                        1.875 |                         0.667 |
| gemini   |        147 |          5     |        0.934 |              0.303 |                    0.068 |           0.213 |                        1.667 |                         0.66  |
| gpt      |        147 |          5     |        0.916 |              0.178 |                    0     |           0.13  |                        1.412 |                         0.782 |


## Label effects: global test per factor (Friedman across profiles)

| model    | factor      |   n_profiles |   friedman_rating_p |   friedman_value_p |   rating_spread_between_levels |   value_ratio_between_levels |
|:---------|:------------|-------------:|--------------------:|-------------------:|-------------------------------:|-----------------------------:|
| claude   | league      |          147 |              0      |                  0 |                         0.3537 |                       5.7195 |
| claude   | nationality |          147 |              0      |                  0 |                         0.1565 |                       1.5696 |
| deepseek | league      |          146 |              0.0001 |                  0 |                         0.2123 |                       4.3824 |
| deepseek | nationality |          143 |              0.0606 |                  0 |                         0.1469 |                       1.5888 |
| gemini   | league      |          147 |              0      |                  0 |                         0.8435 |                       7.5047 |
| gemini   | nationality |          147 |              0.0059 |                  0 |                         0.1633 |                       1.6036 |
| gpt      | league      |          147 |              0      |                  0 |                         0.7891 |                       9.4928 |
| gpt      | nationality |          147 |              0      |                  0 |                         0.1837 |                       1.5114 |


## Label effects: each label versus baseline

| model    | factor      | level              |   n |   d_rating |   d_rating_lo |   d_rating_hi |   p_rating |   d_value_pct |   d_value_pct_lo |   d_value_pct_hi |   d_ready_pp |   d_sign_pp |
|:---------|:------------|:-------------------|----:|-----------:|--------------:|--------------:|-----------:|--------------:|-----------------:|-----------------:|-------------:|------------:|
| claude   | league      | Bundesliga         | 147 |      0.147 |         0.091 |         0.203 |      0     |        42.497 |           35.003 |           50.51  |        8.435 |       1.905 |
| claude   | league      | Eredivisie         | 147 |     -0.084 |        -0.152 |        -0.019 |      0.015 |       -13.508 |          -18.185 |           -8.825 |      -24.218 |      -3.537 |
| claude   | league      | Premier League     | 147 |      0.167 |         0.109 |         0.231 |      0     |       121.951 |          111.698 |          133.661 |       37.687 |       1.905 |
| claude   | league      | Segunda División   | 147 |     -0.146 |        -0.212 |        -0.08  |      0     |       -61.194 |          -63.588 |          -58.704 |      -24.898 |      -4.218 |
| claude   | league      | Swiss Super League | 147 |     -0.186 |        -0.257 |        -0.114 |      0     |       -52.589 |          -55.736 |          -49.01  |      -24.898 |      -4.218 |
| claude   | nationality | Argentina          | 147 |      0.099 |         0.054 |         0.146 |      0     |         0.231 |           -3.406 |            4.333 |        2.313 |       0.544 |
| claude   | nationality | Brazil             | 147 |      0.065 |         0.027 |         0.106 |      0.001 |        18.232 |           13.616 |           22.967 |        0.272 |       0.544 |
| claude   | nationality | Germany            | 147 |      0.106 |         0.059 |         0.159 |      0     |        11.168 |            7.033 |           15.582 |        2.993 |       0.544 |
| claude   | nationality | Japan              | 147 |      0.099 |         0.05  |         0.148 |      0     |       -17.741 |          -21.516 |          -13.843 |       -5.17  |       2.585 |
| claude   | nationality | Nigeria            | 147 |     -0.05  |        -0.099 |         0     |      0.056 |       -24.672 |          -28.492 |          -20.86  |      -10.612 |      -0.136 |
| claude   | nationality | Spain              | 147 |      0.093 |         0.049 |         0.139 |      0     |        14.137 |            9.932 |           18.514 |        1.633 |       1.224 |
| deepseek | league      | Bundesliga         | 147 |      0.107 |         0.039 |         0.179 |      0.003 |        28.133 |           21.757 |           34.707 |       22.585 |       1.905 |
| deepseek | league      | Eredivisie         | 146 |      0.038 |        -0.049 |         0.127 |      0.398 |       -22.346 |          -26.431 |          -18.184 |      -17.945 |     -12.877 |
| deepseek | league      | Premier League     | 147 |      0.025 |        -0.06  |         0.112 |      0.563 |        66.51  |           58.348 |           75.067 |       30.748 |      -1.497 |
| deepseek | league      | Segunda División   | 147 |     -0.097 |        -0.18  |        -0.019 |      0.017 |       -61.999 |          -64.084 |          -59.869 |      -26.395 |     -19.864 |
| deepseek | league      | Swiss Super League | 147 |     -0.097 |        -0.18  |        -0.02  |      0.018 |       -51.726 |          -54.534 |          -48.81  |      -22.313 |     -17.143 |
| deepseek | nationality | Argentina          | 146 |      0.068 |        -0.014 |         0.154 |      0.112 |         4.687 |           -0.247 |            9.388 |        0.822 |       1.918 |
| deepseek | nationality | Brazil             | 147 |      0.12  |         0.04  |         0.207 |      0.005 |        13.558 |            7.786 |           19.704 |        1.497 |       2.585 |
| deepseek | nationality | Germany            | 147 |      0.1   |         0.013 |         0.184 |      0.027 |         7.754 |            2.068 |           13.681 |        6.259 |      -1.497 |
| deepseek | nationality | Japan              | 145 |      0.128 |         0.039 |         0.209 |      0.004 |       -22.328 |          -26.924 |          -17.427 |       -1.241 |       0.552 |
| deepseek | nationality | Nigeria            | 147 |     -0.016 |        -0.101 |         0.071 |      0.722 |       -28.469 |          -32.588 |          -23.923 |       -6.667 |      -4.898 |
| deepseek | nationality | Spain              | 146 |      0.024 |        -0.06  |         0.1   |      0.568 |        10.776 |            4.472 |           16.877 |        5.616 |       2.603 |
| gemini   | league      | Bundesliga         | 147 |      0.341 |         0.264 |         0.422 |      0     |        83.521 |           73.014 |           94.948 |       44.082 |       4.218 |
| gemini   | league      | Eredivisie         | 147 |     -0.196 |        -0.284 |        -0.11  |      0     |       -18.016 |          -22.156 |          -13.503 |      -12.381 |      -5.986 |
| gemini   | league      | Premier League     | 147 |      0.457 |         0.375 |         0.54  |      0     |       186.768 |          166.354 |          208.27  |       55.646 |       4.898 |
| gemini   | league      | Segunda División   | 147 |     -0.325 |        -0.414 |        -0.237 |      0     |       -61.788 |          -64.319 |          -58.875 |      -23.265 |     -12.789 |
| gemini   | league      | Swiss Super League | 147 |     -0.386 |        -0.469 |        -0.301 |      0     |       -53.497 |          -56.871 |          -49.655 |      -24.626 |     -14.83  |
| gemini   | nationality | Argentina          | 147 |     -0.019 |        -0.088 |         0.045 |      0.58  |         2.792 |           -2.074 |            8.051 |       -1.497 |       2.857 |
| gemini   | nationality | Brazil             | 147 |     -0.06  |        -0.14  |         0.02  |      0.151 |         2.503 |           -2.016 |            7.237 |       -2.857 |      -1.224 |
| gemini   | nationality | Germany            | 147 |      0.056 |        -0.026 |         0.139 |      0.193 |        13.42  |            8.07  |           19.348 |       12.109 |       2.857 |
| gemini   | nationality | Japan              | 147 |      0.097 |         0.018 |         0.174 |      0.017 |       -29.274 |          -32.993 |          -25.21  |       -8.299 |      -2.585 |
| gemini   | nationality | Nigeria            | 147 |     -0.067 |        -0.14  |         0.012 |      0.087 |       -20.818 |          -24.485 |          -16.877 |       -2.177 |      -1.224 |
| gemini   | nationality | Spain              | 147 |      0.001 |        -0.073 |         0.071 |      0.971 |         4.099 |           -1.025 |            9.019 |        8.027 |       2.857 |
| gpt      | league      | Bundesliga         | 147 |      0.376 |         0.306 |         0.446 |      0     |       110.187 |          101.962 |          118.637 |       56.599 |       6.803 |
| gpt      | league      | Eredivisie         | 147 |     -0.087 |        -0.15  |        -0.03  |      0.006 |       -17.007 |          -19.923 |          -13.913 |      -14.15  |     -12.245 |
| gpt      | league      | Premier League     | 147 |      0.498 |         0.429 |         0.569 |      0     |       251.691 |          236.405 |          267.626 |       64.762 |       6.122 |
| gpt      | league      | Segunda División   | 147 |     -0.237 |        -0.305 |        -0.17  |      0     |       -62.952 |          -64.471 |          -61.396 |      -18.912 |     -15.646 |
| gpt      | league      | Swiss Super League | 147 |     -0.291 |        -0.358 |        -0.224 |      0     |       -53.027 |          -54.753 |          -51.215 |      -19.592 |     -15.646 |
| gpt      | nationality | Argentina          | 147 |      0.035 |        -0.022 |         0.093 |      0.23  |        -1.537 |           -4.391 |            1.271 |        0.816 |       1.361 |
| gpt      | nationality | Brazil             | 147 |      0.015 |        -0.05  |         0.08  |      0.652 |         6.604 |            3.606 |            9.805 |        3.537 |       1.361 |
| gpt      | nationality | Germany            | 147 |      0.069 |         0.018 |         0.125 |      0.011 |        14.909 |           11.171 |           18.495 |        4.898 |       2.721 |
| gpt      | nationality | Japan              | 147 |      0.001 |        -0.065 |         0.067 |      0.968 |       -22.107 |          -24.354 |          -19.723 |       -1.905 |       0.68  |
| gpt      | nationality | Nigeria            | 147 |     -0.073 |        -0.131 |        -0.018 |      0.011 |       -23.974 |          -26.406 |          -21.512 |       -4.626 |      -2.721 |
| gpt      | nationality | Spain              | 147 |      0.11  |         0.05  |         0.169 |      0     |        14.273 |           11.01  |           17.515 |        4.218 |       4.762 |


## Numerical faithfulness

| model    |   responses |   claims_per_response |   unsupported_claim_rate |   share_responses_with_unsupported |
|:---------|------------:|----------------------:|-------------------------:|-----------------------------------:|
| claude   |        2352 |                 5.855 |                    0.002 |                              0.011 |
| deepseek |        2346 |                 4.795 |                    0.001 |                              0.003 |
| gemini   |        2352 |                 2.898 |                    0.005 |                              0.015 |
| gpt      |        2352 |                11.19  |                    0.01  |                              0.097 |


## Label versus real performance

| model    |   perf_low_to_high_rating |   perf_low_to_high_value_pct |   label_max_rating | label_max_level   |   label_value_spread_pct | label_value_best   | label_value_worst   |
|:---------|--------------------------:|-----------------------------:|-------------------:|:------------------|-------------------------:|:-------------------|:--------------------|
| claude   |                     2.098 |                      323.453 |              0.167 | Premier League    |                  471.953 | Premier League     | Segunda División    |
| deepseek |                     2.053 |                      257.176 |              0.128 | Japan             |                  338.173 | Premier League     | Segunda División    |
| gemini   |                     3.02  |                      615.342 |              0.457 | Premier League    |                  650.472 | Premier League     | Segunda División    |
| gpt      |                     1.943 |                      242.741 |              0.498 | Premier League    |                  849.283 | Premier League     | Segunda División    |


## Mixed models (rating ~ level + (1|profile))

| model    | factor      | level_vs_reference   | reference   |    coef |      p |
|:---------|:------------|:---------------------|:------------|--------:|-------:|
| claude   | league      | Eredivisie           | Bundesliga  | -0.2313 | 0      |
| claude   | league      | Premier League       | Bundesliga  |  0.0204 | 0.5726 |
| claude   | league      | Segunda División     | Bundesliga  | -0.2925 | 0      |
| claude   | league      | Swiss Super League   | Bundesliga  | -0.3333 | 0      |
| claude   | nationality | Brazil               | Argentina   | -0.034  | 0.2217 |
| claude   | nationality | Germany              | Argentina   |  0.0068 | 0.8069 |
| claude   | nationality | Japan                | Argentina   | -0      | 1      |
| claude   | nationality | Nigeria              | Argentina   | -0.1497 | 0      |
| claude   | nationality | Spain                | Argentina   | -0.0068 | 0.8069 |
| deepseek | league      | Eredivisie           | Bundesliga  | -0.0729 | 0.1601 |
| deepseek | league      | Premier League       | Bundesliga  | -0.0816 | 0.1149 |
| deepseek | league      | Segunda División     | Bundesliga  | -0.2041 | 0.0001 |
| deepseek | league      | Swiss Super League   | Bundesliga  | -0.2041 | 0.0001 |
| deepseek | nationality | Brazil               | Argentina   |  0.0551 | 0.3272 |
| deepseek | nationality | Germany              | Argentina   |  0.0347 | 0.5372 |
| deepseek | nationality | Japan                | Argentina   |  0.0624 | 0.2698 |
| deepseek | nationality | Nigeria              | Argentina   | -0.0809 | 0.1504 |
| deepseek | nationality | Spain                | Argentina   | -0.043  | 0.4453 |
| gemini   | league      | Eredivisie           | Bundesliga  | -0.5374 | 0      |
| gemini   | league      | Premier League       | Bundesliga  |  0.1156 | 0.0257 |
| gemini   | league      | Segunda División     | Bundesliga  | -0.6667 | 0      |
| gemini   | league      | Swiss Super League   | Bundesliga  | -0.7279 | 0      |
| gemini   | nationality | Brazil               | Argentina   | -0.0408 | 0.4187 |
| gemini   | nationality | Germany              | Argentina   |  0.0748 | 0.1382 |
| gemini   | nationality | Japan                | Argentina   |  0.1156 | 0.0219 |
| gemini   | nationality | Nigeria              | Argentina   | -0.0476 | 0.3454 |
| gemini   | nationality | Spain                | Argentina   |  0.0204 | 0.6859 |
| gpt      | league      | Eredivisie           | Bundesliga  | -0.4626 | 0      |
| gpt      | league      | Premier League       | Bundesliga  |  0.1224 | 0.0027 |
| gpt      | league      | Segunda División     | Bundesliga  | -0.6122 | 0      |
| gpt      | league      | Swiss Super League   | Bundesliga  | -0.6667 | 0      |
| gpt      | nationality | Brazil               | Argentina   | -0.0204 | 0.5791 |
| gpt      | nationality | Germany              | Argentina   |  0.034  | 0.3552 |
| gpt      | nationality | Japan                | Argentina   | -0.034  | 0.3552 |
| gpt      | nationality | Nigeria              | Argentina   | -0.1088 | 0.0031 |
| gpt      | nationality | Spain                | Argentina   |  0.0748 | 0.0419 |

