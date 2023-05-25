# Demo

## 主要代码树

```shell
.
├── README.md
├── Screen
│   ├── NodeDescriber.py——界面解析包
│   ├── NodeDescriberManager.py——界面解析包
│   ├── Utility.py——界面解析包
│   ├── WindowStructure.py——界面解析包
│   ├── init.py——接受手机端发送来的数据时的处理类，主要包括Screen类
│   └── process.py——对收到的界面信息做处理（低优先级）
├── app.py——（后端的Flask框架）
└── src
    └── llm.py——整体框架的实现，位于LLM类中，具体见注释
```

# 形式化描述

# 输入输出

输入为自然语言的任务描述 $d$

输出为$s(c_{\pi}|p_i,a_i,e_i)$，其中：

-   $P$ (Pages): 所有页面的集合，某一页面满足$p \in P$，在任务执行过程中是非完备️集合
-   $A$ （Actions）: 预先定义好的操作集合，是有限集，任一操作$a \in A$，是一元操作集合，例如点击(Click)、长按（Long Press）等。
-   $E$（Elements):当前页面的控件集合，是有限集，选择的控件$e \in E$
-   $c_\pi$表示每一步推导得到新页面的概率。$c_\pi$表示在$p_{i-1}$中做出决策，转到$p_i$的概率

而输出表示在当前页面$p_i$上选择控件$e_i$进行操作$a_i$得到的新页面，则有

$$
p_{i+1} = s(c_{\pi}|p_i,a_i,e_i)
$$

因此得到操作序列$\{p_1,p_2\cdots p_k\}_d$,要求该序列完成任务描述$d$

# 挑战

-   ~~要将页面信息以有序、简洁、完备的形式组织后以文本形式交给LLM处理；~~
-   **非完备性：**
    -   界面的跳转关系是非完备的，每进行一步所带来的新界面未知
        -   $P$是一个有向图，节点表示页面，边表示操作，图非完备，我们希望找到正确路径。
        -   要有启发性策略
    -   非完备性导致决策可能陷入局部最优解
        -
-   **正确性：**
    -   如何判断任务的结束？
        -   对应的：如何判断任务执行失败（异常检测）
-   **鲁棒性：**
    -   能否尽可能避免进入错误路径？
        -   知识积累⇒**可学习性**
    -   当进入错误路径时，怎么回溯？
    -   当发生任何错误情况，不仅仅是回溯，应该调整策略，执行反馈。

# 函数描述

$$
s(c_{\pi}|p_i,a_i,e_i)=\argmax_{e \in E,a \in A}\{C(E,A|p_i)\}
$$

其中$C(E,A|p_i)$表示在当前页面$p_i$上每一个控件$e$执行对应操作的概率分布，它由以下部分决定

> 首先，我们定义
>
> -   $\delta(e_k|p_1,p_2,\cdots,p_i,d)$**表示由LLM给出的根据**$d$**在当前页面**$p_i$**上选择控件**$e_k$**的概率。**
>     -   基本方法
> -   $\varepsilon(e_k|p_i,d,\tilde{p}_{i+1},\gamma)$** 表示【在当前页面**$p_i$**上进行某种操作，并且可能进入**新的页面（预测）**】对完成任务**$d$**的贡献。其中**$\gamma$**表示**惩罚因子**。**
>     -   该项独立于LLM的决策之外，评估候选项对完成任务的帮助大小
>     -   预测的目的是解决不完备性，使得尽可能完备；
>     -   惩罚因子$\gamma$为解决鲁棒性，即它可能承担一些回溯/反馈的作用，例如【上次在这里走错了选择了$A$，现在再回来做选择，$A$的惩罚因子应较大，不希望被选中】，具体在机制中实现。
> -   $confidence(e_k|p_i,d)$**表示在任务**$d$**下当前页面**$p_i$**选择某元素**$e_k$**的置信度。**
>     -   该项的含义是：某个控件$e_k$的置信度有多高？点击之后是否大概率出错？例如【即便从LLM的角度看来，“设置”和“调整微信铃声”的相关性不高，但是“设置”按钮点击后出错的概率不大，可以放心尝试；相比较之下，“隐私”和“通知”相比，点击后出错的概率就非常大，不应该尝试】
>     -   另外一种情况：【我通过知识积累，或者错误经验，明知应该到设置中去寻找，就应该将其他选项的error率提高，设置的error率降低】，对应知识积累的机制
>     -   从控件本身的性质来说，例如【Tab栏选中的概率，联系人选中的概率可能会有区别】
>     -   该项的目的是解决鲁棒性，尽可能避免出错，更一般的，与可学习性相关。

$$
c(e_i|p_i,d)=\delta(e_k|p_1,p_2,\cdots,p_i,d)*\varepsilon(e_k|p_i,d,\tilde{p}_{i+1})*confidence(e_k|p_i,d)
$$

# 机制Mechanism

## 预测

#### 应对的挑战：

-   降低非完备性带来的风险

#### 描述

$$
\tilde{p}_{i+1}=predict(p_i,e_k)\mid fact(p_i,e_k)
$$

## 知识积累

#### 应对的挑战

-   解决非完备性
-   解决鲁棒性中的：尽可能避免进入异常路径

#### 描述

$$
facts = \{<p_i,e_k,p_{i+1}>\}
$$

## 正常/异常检测

#### 应对的挑战

-   解决正确性问题

#### 描述

两种策略处理

Value 和 Vote

## 异常处理——回退

## 异常处理——策略调整

## Beam Search

[任务集合](
