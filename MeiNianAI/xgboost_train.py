import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import operator
import re
import xgboost as xgb
from sklearn.model_selection import GridSearchCV
import win_unicode_console
win_unicode_console.enable()


def train_map(label):
    if label == '弃查' or label == '未查':
        return '0'
    else:
        return label


def re_match(x):
    reg_label = re.findall(re.compile('\d.*\d'), str(x))
    if reg_label:
        return reg_label[0]
    else:
        return x


def deal_train_label(train_label):
    train_label['收缩压'] = train_label['收缩压'].apply(train_map)
    train_label['舒张压'] = train_label['舒张压'].apply(train_map)
    train_label['血清甘油三酯'] = train_label['血清甘油三酯'].apply(train_map)
    train_label['血清高密度脂蛋白'] = train_label['血清高密度脂蛋白'].apply(train_map)
    # print(train_label['血清高密度脂蛋白'].isnull().any())
    # train_label['血清低密度脂蛋白'] = train_label['血清低密度脂蛋白'].apply(train_map)

    # train_label['收缩压'] = train_label['收缩压'].apply(re_match)
    # train_label['舒张压'] = train_label['舒张压'].apply(re_match)
    train_label['血清甘油三酯'] = train_label['血清甘油三酯'].apply(re_match)
    # train_label['血清高密度脂蛋白'] = train_label['血清高密度脂蛋白'].apply(re_match)
    # 标签中有负数，需要转化，否则在训练时会出错，因为使用了'neg_mean_squared_log_error'评价指标，预测值不能为负数
    train_label['血清低密度脂蛋白'] = train_label['血清低密度脂蛋白'].apply(
        lambda x: abs(int(x)) if int(x) < 0 else x)

    train_label_shousuo = list(map(float, train_label['收缩压'].values))
    train_label_shuzhang = list(map(float, train_label['舒张压'].values))
    train_label_ganyousanzhi = list(map(float, train_label['血清甘油三酯'].values))
    train_label_gaomiduzhidanbai = list(
        map(float, train_label['血清高密度脂蛋白'].values))
    train_label_dimiduzhidanbai = list(
        map(float, train_label['血清低密度脂蛋白'].values))

    return train_label_shousuo, train_label_shuzhang, train_label_ganyousanzhi, train_label_gaomiduzhidanbai, train_label_dimiduzhidanbai


def xgb_cv(X_train, Y_train):
    cv_params = {
        # 'n_estimators': range(245, 270, 5),
        # 'max_depth': range(8, 12, 1),
        # 'min_child_weight': [5],
        # 'subsample': [0.55, 0.6, 0.65],
        # 'colsample_bytree': [0.7, 0.75, 0.8],
        # 'gamma': [0.5, 0.6, 0.7, 0.8],
        # 'reg_alpha': [6, 7, 8, 9],
        # 'reg_lambda': [6],
        # 'learning_rate': [0.01, 0.05, 0.1, 0.15]
    }
    model = xgb.XGBRegressor(
        learning_rate=0.05,
        n_estimators=260,
        max_depth=8,
        min_child_weight=5,
        seed=0,
        subsample=0.65,
        colsample_bytree=0.7,
        gamma=0.8,
        reg_alpha=6,
        reg_lambda=6,
        metrics='auc')
    optimized_GBM = GridSearchCV(
        estimator=model,
        param_grid=cv_params,
        scoring='neg_mean_squared_log_error',
        cv=5,
        verbose=1,
        n_jobs=4)
    optimized_GBM.fit(X_train, Y_train)
    evalute_result = optimized_GBM.grid_scores_
    print('每轮迭代运行结果:{0}'.format(evalute_result))
    print('参数的最佳取值：{0}'.format(optimized_GBM.best_params_))
    print('最佳模型得分:{0}'.format(optimized_GBM.best_score_))


def model_process(X_train, train_label_shousuo, train_label_shuzhang,
                  train_label_ganyousanzhi, train_label_gaomiduzhidanbai,
                  train_label_dimiduzhidanbai, X_test):
    # XGBoost训练过程
    #**************收缩压模型**************#
    model_shousuoya = xgb.XGBRegressor(
        learning_rate=0.1,
        n_estimators=145,
        max_depth=5,
        min_child_weight=8,
        seed=0,
        subsample=0.7,
        colsample_bytree=0.6,
        gamma=0.2,
        reg_alpha=6,
        reg_lambda=6,
        metrics='auc')

    model_shousuoya.fit(X_train, train_label_shousuo)

    # 对测试集进行预测
    predict_shousuoya = model_shousuoya.predict(X_test)

    #**************舒张压模型**************#
    model_shuzhangya = xgb.XGBRegressor(
        learning_rate=0.05,
        n_estimators=100,
        max_depth=7,
        min_child_weight=6,
        seed=0,
        subsample=0.65,
        colsample_bytree=0.7,
        gamma=0.8,
        reg_alpha=6,
        reg_lambda=6,
        metrics='auc')

    model_shuzhangya.fit(X_train, train_label_shuzhang)

    # 对测试集进行预测
    predict_shuzhangya = model_shuzhangya.predict(X_test)

    #**************血清甘油三酯模型**************#
    model_ganyousanzhi = xgb.XGBRegressor(
        learning_rate=0.1,
        n_estimators=20,
        max_depth=5,
        min_child_weight=6,
        seed=0,
        subsample=0.75,
        colsample_bytree=0.6,
        gamma=0.6,
        reg_alpha=6,
        reg_lambda=6,
        metrics='auc')

    model_ganyousanzhi.fit(X_train, train_label_ganyousanzhi)

    # 对测试集进行预测
    predict_ganyousanzhi = model_ganyousanzhi.predict(X_test)

    #**************血清高密度脂蛋白模型**************#
    model_gaomiduzhidanbai = xgb.XGBRegressor(
        learning_rate=0.05,
        n_estimators=260,
        max_depth=8,
        min_child_weight=5,
        seed=0,
        subsample=0.65,
        colsample_bytree=0.7,
        gamma=0.8,
        reg_alpha=6,
        reg_lambda=6,
        metrics='auc')

    model_gaomiduzhidanbai.fit(X_train, train_label_gaomiduzhidanbai)

    # 对测试集进行预测
    predict_gaomiduzhidanbai = model_gaomiduzhidanbai.predict(X_test)

    #**************血清低密度脂蛋白模型**************#
    model_dimiduzhidanbai = xgb.XGBRegressor(
        learning_rate=0.05,
        n_estimators=160,
        max_depth=7,
        min_child_weight=7,
        seed=0,
        subsample=0.7,
        colsample_bytree=0.6,
        gamma=0.2,
        reg_alpha=6,
        reg_lambda=6,
        metrics='auc')

    model_dimiduzhidanbai.fit(X_train, train_label_dimiduzhidanbai)

    # 对测试集进行预测
    predict_dimiduzhidanbai = model_dimiduzhidanbai.predict(X_test)

    test_label['shousuoya'] = predict_shousuoya
    test_label['shuzhangya'] = predict_shuzhangya
    test_label['ganyousanzhi'] = predict_ganyousanzhi
    test_label['gaomiduzhidanbai'] = predict_gaomiduzhidanbai
    test_label['dimiduzhidanbai'] = predict_dimiduzhidanbai

    test_label.to_csv('submit_result.csv', index=False, header=None)


def ceate_feature_map(features):
    outfile = open('xgb.fmap', 'w')
    i = 0
    for feat in features:
        outfile.write('{0}\t{1}\tq\n'.format(i, feat))
        i += 1
    outfile.close()


def get_feature_importance(X_train, train_label_ganyousanzhi):
    features = X_train.columns.tolist()
    ceate_feature_map(features)
    #**************血清甘油三酯模型**************#
    params = {
        'silent': True,
        'learning_rate': 0.1,
        'n_estimators': 20,
        'max_depth': 5,
        'min_child_weigh': 6,
        'seed': 0,
        'subsample': 0.75,
        'colsample_bytree': 0.6,
        'gamma': 0.6,
        'reg_alpha': 6,
        'reg_lambda': 6,
        'metric': 'rmse'
    }

    xgbtrain = xgb.DMatrix(X_train, label=train_label_ganyousanzhi)
    watchlist = [(xgbtrain, 'train')]
    bst = xgb.train(
        params,
        xgbtrain,
        num_boost_round=200,
        evals=watchlist,
        early_stopping_rounds=50)

    importance = bst.get_fscore(fmap='xgb.fmap')
    importance = sorted(importance.items(), key=operator.itemgetter(1))

    df = pd.DataFrame(importance, columns=['feature', 'fscore'])
    df['fscore'] = df['fscore'] / df['fscore'].sum()
    df.plot(
        kind='barh', x='feature', y='fscore', legend=False, figsize=(16, 10))
    plt.title('XGBoost Feature Importance')
    plt.xlabel('relative importance')
    plt.show()


if __name__ == '__main__':
    print("***************************开始导入数据集*******************************")
    feature_train_data = pd.read_csv('data/data_total_train.csv')
    feature_test_data = pd.read_csv('data/data_total_test.csv')
    train_label = pd.read_csv(
        'data/meinian_round1_train_20180408.csv', encoding='gbk')
    test_label = pd.read_csv(
        'data/meinian_round1_test_a_20180409.csv', encoding='gbk')

    print('训练集的列数为：{0}，行数为：{1}'.format(feature_train_data.columns.size,
                                       feature_train_data.iloc[:, 0].size))
    print('测试集的列数为：{0}，行数为：{1}'.format(feature_test_data.columns.size,
                                       feature_test_data.iloc[:, 0].size))
    # print(feature_train_data.columns)

    X_train = feature_train_data.drop('vid', axis=1)
    X_test = feature_test_data.drop('vid', axis=1)

    test_label.drop(
        ['收缩压', '舒张压', '血清甘油三酯', '血清高密度脂蛋白', '血清低密度脂蛋白'], axis=1, inplace=True)
    # print(test_label)
    # print(train_label['血清低密度脂蛋白'].isnull().any())
    # print(train_label['收缩压'].value_counts())
    print("***********************开始处理训练集标签脏数据*************************")
    train_label_shousuo, train_label_shuzhang, train_label_ganyousanzhi, train_label_gaomiduzhidanbai, train_label_dimiduzhidanbai = deal_train_label(
        train_label)
    # print(np.nan in train_label_dimiduzhidanbai)
    # print(train_label[train_label['血清甘油三酯'] == '2.2.8'])
    print("训练集标签脏数据处理完毕!")
    print("****************************特征重要度评分******************************")
    get_feature_importance(X_train, train_label_ganyousanzhi)
    print("****************************开始训练模型********************************")
    # print(X_train)
    # xgb_cv(X_train, train_label_shousuo)
    # xgb_cv(X_train, train_label_shuzhang)
    # xgb_cv(X_train, train_label_ganyousanzhi)
    # xgb_cv(X_train, train_label_gaomiduzhidanbai)
    # xgb_cv(X_train, train_label_dimiduzhidanbai)
    print("****************************开始预测结果********************************")
    # model_process(X_train, train_label_shousuo, train_label_shuzhang,
    #               train_label_ganyousanzhi, train_label_gaomiduzhidanbai,
    #               train_label_dimiduzhidanbai, X_test)
    print(
        "*******************************程序结束*********************************")
