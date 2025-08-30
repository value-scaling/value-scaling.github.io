Card 1: [authors] [utd scaling arxiv] [poster] [[code](https://github.com/prestonfu/qscaled)]

Card 2 (new!): [authors] [model scaling arxiv] [code]

**[motivation gif]**

Large models are slow and expensive to train, so we like to prototype research ideas on small scales before scaling up to larger budgets. This workflow assumes some guarantee of _predictability._ For example, the field has shown that language model pretraining [is predictable](https://arxiv.org/abs/2001.08361) — provided the "right" design decisions.

Scaling law research typically follows three steps:

1. Within a budget, find the best-performing configuration for a given method (model architecture, algorithm), and verify that the _configuration and performance_ scale predictably with the budget.
2. Repeat Step 1 for multiple methods, and select the one with the best predicted extrapolated performance.
3. Extrapolate this method's best-performing configuration to larger budgets, and check that performance matches the prediction.

In supervised learning, these steps are enabled by the fact that training minimizes a loss over a fixed data distribution. This stability makes Step 1 tractable: once a configuration is tuned, its scaling behavior is smooth enough to trust the subsequent steps.

In online reinforcement learning (RL), however, Step 1 is far harder. Online RL updates its own data distribution over the course of training, adding instability at scale. This instability is the main obstacle to establishing predictability and, in turn, to enabling Steps 2 and 3.

We challenge this view and show that value-based RL does admit predictable scaling, with the right design decisions. By resolving the central difficulty of Step 1, we unlock the rest of the workflow.

![h1stand_3d.mp4](/assets/images/h1stand_3d.mp4 "**Figure n.** Step 1: With the right configuration, data efficiency is predictable with respect to scaling axes, unlocking compute-optimal scaling."){width=400px}

## Framework

Scaling laws answer this question:

> _Given a large, unseen budget of data and compute, how can we achieve the best possible performance?_

Let's examine the case of supervised learning, where scaling laws have already proved successful. To define the question more carefully: (i) what constitutes the budget, and (ii) what is our performance metric?

(i) A training compute (FLOPs) budget can be allocated along four axes:

$\text{compute} \propto \text{dataset size} \times \text{epochs} \times \text{batch size} \times \text{model size}$

(ii) Performance is measured by the test loss.

Within this framework, the field of supervised learning has come to several key conclusions:

- Large models should not be trained to the lowest possible loss to be compute-optimal (Kaplan, 2020).
- Scaling the batch size is useful for obtaining a more accurate estimate of the true gradient. However, there is a critical batch size in supervised learning, beyond which further increases in batch size yield minimal returns (McCandlish, 2018).
- In data-constrained settings, you can train for [up to 4 epochs](https://arxiv.org/abs/2305.16264) before training on the same data yields diminishing returns (Muennighoff, 2023).

Scaling law research proved fruitful once it leveraged _all of these observations together_. This enabled simple [power laws](https://arxiv.org/abs/2001.08361) (Kaplan, 2020) forecasting the loss in terms of model size and dataset size. Assuming the right batch size and epoch count, balancing between model size and dataset size laid the groundwork to train large models [compute-optimally](https://arxiv.org/abs/2203.15556) (Hoffman, 2022).

Similarly, RL scaling law research must first understand scaling along each axis before scaling them jointly.

## What makes RL scaling laws different?

Let's revisit our two prerequisite questions:

(i) In supervised learning, our data is collected a priori. Training assumes that the data is sampled i.i.d. from the dataset, and compute is spent uniformly over the data. In RL, we decompose the budget into two components: resources $\mathcal D$ ("data") spent collecting data by interacting with an environment, and resources $\mathcal C$ ("compute") spent training on the data. Although the amount of compute $\mathcal C$ is proportional to the amount of collected data $\mathcal D$, in practice both procedures consume resources such as wall-clock time, and it is beneficial to define them separately. Depending on the domain of interest (e.g. language models or robotics), data will vary widely in terms of collection cost. Accordingly, we can define a budget $\mathcal C + \delta \cdot \mathcal D$, where $\delta$ is defined separately for each use case.

(ii) The performance metric is an agent's Monte Carlo returns when interacting with an environment.

This setup gives us our problem statement:

> _Given a limited budget_ $\mathcal F_0$_, which may be a combination $\mathcal C + \delta \cdot \mathcal D$ of compute and data, how do we achieve the best possible performance_ $J^*$_?_

In practice, this problem is hard to answer directly, since the reward structure can vary significantly across environments. Instead, we'll consider the dual problem. That is, we can define **data efficiency** $\mathcal D_J$ and **compute efficiency** $\mathcal C_J$ as the amounts of data and compute spent to achieve performance $J$, respectively. Then, at the optimal $J^*$, we will have used up exactly the allocated budget: $\mathcal F_0 = \mathcal C_{J^*} + \delta \cdot \mathcal D_{J^*}$. So, we can instead estimate $\mathcal D_J$ and $\mathcal C_J$ for multiple $J$, then select the largest $J$ fitting within the budget.

> _Given a performance threshold_ $J$, _how can we allocate our resources to minimize the budget_ $\mathcal C_J + \delta \cdot \mathcal D_J$_?_

Scaling laws have been [studied](https://arxiv.org/abs/2301.13442) for **on-policy algorithms** (Hilton, 2023), like PPO and GRPO. On-policy algorithms iteratively collect a batch of trajectories from the current policy $\pi$, score those trajectories, and take a gradient step toward high-scoring trajectories (perhaps subject to constraints). At each iteration, once the update is done, the data must be thrown away (**do we need a footnote?**), and a new batch is collected from the new policy.

This last line highlights that on-policy algorithms are not data-efficient: we instead need off-policy RL algorithms, which able to learn from data collected by policies other than $\pi$. In practice, however, scaling off-policy RL is tricky.

### Off-policy RL

Modern instantiations of off-policy RL typically use a **value function** $Q_\theta(s,a)$, which decouple data collection from gradient updates. The learned value function is agnostic to the policy used to collect state-action transitions – instead, these transitions are sampled from a replay buffer $\mathcal P$. In principle, the replay buffer can consist of _any_ transitions – even if collected by another agent. In practice, the value network is bootstrapped by regressing onto a moving **temporal distance (TD)-target** $r(s,a) + \gamma \bar Q(s', a')$, where $\bar Q$ is produced via a moving average of the parameters of $Q_\theta$ and is used for training stability. Putting this all together, the value function takes gradient steps on the **TD error**,

$L(\theta) = \mathbb{E}_{(s, a, s') \sim \mathcal{P}, a' \sim \pi(\cdot|s')}\left[ \left(r(s, a) + \gamma \bar{Q}(s', a') - Q_\theta(s, a) \right)^2\right]$

However, bootstrapping onto TD-targets introduces additional scaling complexities:

- The TD-targets are moving because the parameters of $\bar Q$ are dependent on those of $Q$.
- Replay introduces staleness because we revisit old transitions.

However, this latter mechanic is exactly what makes TD-learning compelling in data-constrained regimes like robotics: we can reuse expensive experience many times. Intuitively, we can scale compute for a given amount of data by just taking multiple gradient steps on each batch sampled from the replay buffer. This knob is the **updates-to-data ratio (UTD)**.

Going back to question (i), we now have:

$\mathcal C_J \propto \mathcal D_J  \times \text{UTD} \times \text{batch size} \times \text{model size}$

Increasing the UTD ratio tends to improve performance for small UTD, but doing so naively can [eventually worsen](https://arxiv.org/abs/2205.07802) performance (Nikishin, 2022). How can we combat this?

**We argue that off-policy RL training is limited by overfitting.** Specifically:

- For UTD scaling, we define "overfitting" as a metric for training data staleness.
- For model size scaling, we define it as a metric for value function generalization.

Empirically, we find that using the correct batch size can mitigate overfitting in each case and enables scaling to higher UTD and model sizes.

## How do I set my hyperparameters?

A key ingredient enabling language model scaling laws is the variety of theory and [practice](https://arxiv.org/abs/1404.5997) (Krizhevsky, 2014) establishing the relationship between optimal [batch size](https://www.jmlr.org/papers/v20/18-789.html) (Shallue, 2018), learning rate, and [optimizer](https://proceedings.neurips.cc/paper/2019/hash/e0eacd983971634327ae1819ea8b6214-Abstract.html) (Zhang, 2019). Put together, these trends enabled [hyperparameter transfer](https://arxiv.org/abs/2203.03466) (Yang, 2022) to unseen model sizes.

In our answer to this question, we unlock several surprising findings on off-policy RL training dynamics, which we later leverage to scale UTD and model size effectively.

### …when I scale the UTD?

```markdown
Box linking to UTD scaling paper
```

Let's first look at the case of UTD-only scaling at a constant model size. Empirically, we find that performance is most sensitive to changes in batch size and learning rate, and we'll focus on these hyperparameters.

Let's define "overfitting" as the difference between TD errors on data sampled uniformly at random from the replay buffer $\mathcal P$ and the data most recently added to the replay buffer. Intuitively, high UTD and high batch size both see the "average" sample more times and overfit to those samples. This results in higher relative TD error on data recently collected by the policy $\pi$. We also observe this empirically! **To counteract this effect, we decrease the batch size for higher UTD.**

![image.png](attachment:eb6c80d9-139f-4902-be17-8a766f0c5fa9:image.png)

**Figure n:** Overfitting increases with both UTD and batch size.

We also observe that high UTD ratios lead to **plasticity loss**, i.e. the inability to fit TD targets appearing later in training as a result of fitting them too much early on in training. Similarly, we observed that higher learning rates lead to high-magnitude updates against the target, moving the parameters to a state that would suffer from difficulty in fitting subsequent targets. Following [prior work](https://openreview.net/forum?id=OpC-9aBBVJe), we empirically find that one diagnosis for plasticity loss is large parameter norm in the Q-network: increasing either UTD or learning rate corresponds to larger parameter norm. **To counteract this effect, we decrease the learning rate for higher UTD, empirically following roughly a power law.**

![image.png](attachment:bb7379d4-d7f6-4884-a26f-4cc458373649:image.png)

**Figure n:** Parameter norm, a proxy for plasticity loss, increases with both UTD and learning rate.

```markdown
Takeaways:

- Decrease batch size with UTD. In our first paper, we showed empirically that it should
  decay as a power law.
- Decrease learning rate with UTD, also empirically following a power law.
```

### …when I scale the model size?

```markdown
Box linking to UTD+N scaling paper
```

Let's now look at the case of model size scaling at a constant UTD.

**How does overfitting manifest with model size scaling?** Here, instead of a metric for staleness, we'll directly measure the Q-network's generalization capabilities. To do so, we'll measure the TD error on both the training data and a held-out validation set of transitions drawn from a replay buffer with the same distribution (see Appendix B of [our new paper](https://arxiv.org/abs/2508.14881) for more details). It's helpful to look at these curves over the course of training, since in the practical implementation of TD-learning, value functions rarely fully fit the moving TD-targets. We show these learning curves in Figure n.

[loss2x2_crawl.mp4](attachment:7c5524ca-43df-407e-ab2e-1ef2bd45bb67:loss2x2_crawl.mp4)

**Figure n:** Training and validation TD-errors reduce as model size increase. However, for smaller models, a larger batch size results in a higher final TD-error. This illustrates the role of batch size in modulating overfitting with TD-learning.

Unsurprisingly, increasing the batch size improves training TD-error. However, the effect on validation TD-error is more nuanced and depends on the model size. Why does this happen?

**Conceptual view:** We argue that this is explained by the use of target networks in TD-learning, and coin this phenomenon **TD-overfitting**. Consider a smaller value function. Due to its low representational capacity, a model would entangle features used for predicting Q-values across multiple (state, action) pairs. As we scale up the batch size, this issue is exacerbated since these incorrect gradient updates become more "directed". Fitting the Q-function, and hence the TD-targets, on some transitions comes at the expense of others.

By contrast, larger value functions produce features that can decouple its predictions across transitions, leading to improved generalization at larger batch sizes.

![image.png](attachment:b335cc9e-8611-4219-b7ab-6fc7df774e6f:image.png)

**Figure n:** Small models perform better with smaller batch sizes, which result in noisy updates, due to more directed gradient updates onto low-quality TD-targets. Larger models produce higher-quality TD targets and benefit from regressing to these targets better with larger batch sizes.

**Analysis:** Check out [our new paper](https://arxiv.org/abs/2508.14881) (Section 5.3) for some really cool analysis of this phenomenon!

**So, how do I set my batch size?** Empirically, we observe that the best batch size increases with model size, but eventually reaches an upward asymptote. Check out [our new paper](https://arxiv.org/abs/2508.14881) for our fit equation! Empirically we do not observe a significant interaction effect between UTD and model size, i.e. our fit factorizes into a power law decay in UTD and an upward asymptote in model size.

**How about other key hyperparameters?** In [our new paper](https://arxiv.org/abs/2508.14881), we additionally consider the effect of learning rate (Appendix D.2) and the target update rate (Appendix D.3). For "reasonable" selections of those hyperparameters, we found that data efficiency was most sensitive to changes in batch size.

```markdown
Takeaways:

- TD-overfitting: Smaller models produce TD-targets that generalize poorly, and are
  hurt by large batch sizes.
- Larger models produce TD-targets that generalize well, and benefit from large
  batch sizes.
- The best batch size increases with model size, but is bounded above by an asymptote.
```

## Budget-optimal UTD scaling

```markdown
Box linking to UTD scaling paper
```

As before, we'll first consider UTD-only scaling at a constant model size. Armed with the best-choice batch size and learning rate, we can optimize the data efficiency. Empirically, we find that **data efficiency scales as a power law with respect to UTD, across multiple domains, tasks, and algorithms**!

![image.png](attachment:1525c1ec-0381-4839-be59-7e5ba87db711:image.png)

**Figure n:** Data efficiency scales as a power law with respect to UTD. Leveraging the batch size and learning rate fits asymptotically outperforms a constant baseline.

Finally, we are in a position to answer our question:

> _Given a performance threshold_ $J$, _what is the minimum achievable budget_ $\mathcal C_J + \delta \cdot \mathcal D_J$\*, where the **data efficiency\*** $\mathcal D_J$ \*and **compute efficiency\*** $\mathcal C_J$ _are the amounts of data and compute spent to achieve performance_ $J$_?_

**Step 1:** We can consider the amount of compute, in FLOPs, required to achieve a given performance threshold. For each threshold, there is a Pareto frontier defining the tradeoff between data and compute requirements, and the UTD defines the position along this curve. Along this Pareto frontier, there is a unique budget-minimizing selection of UTD. In our first paper, we showed that the budget-optimal partition between data and compute is predictable, as well as the budget-optimal UTD itself!

[\_oleh - 1889016893140516880.mp4](attachment:d319bfea-1537-46e7-a7c7-6a3fd33b4717:_oleh_-_1889016893140516880.mp4)

**Step 3:** We find that the budget-optimal UTD extrapolates well to larger budgets! **Our method lets you predict the best data-compute tradeoff at unseen budgets.**

![image.png](attachment:39eff269-a2b6-4fee-a1ad-8fd0b69e83dc:image.png)

```markdown
Takeaways:

- Leveraging the batch size and learning rate fits, we find predictable power-law
  scaling in data efficiency versus UTD!
- For each threshold, the UTD defines a Pareto frontier between data and compute
  requirements.
- The budget-optimal UTD is predictable, following a power law in budget.
```

## Budget-optimal scaling for UTD and model size

```markdown
Box linking to UTD+N scaling paper
```

**Step 1:** Now, we'll additionally leverage our understanding of TD-overfitting via our batch size fit. Assuming this fit, we find that **data efficiency scales as a sum of power laws with respect to the UTD and model size**. (In Section 6 of [our new paper](https://arxiv.org/abs/2508.14881), we also run a sensitivity analysis to show the importance of using the right batch size.)

[data_iso_contour.mp4](attachment:2934d9fb-ffab-4211-8912-1811754d1f85:data_iso_contour.mp4)

**Figure n:** Each contour is the curve attaining the same fitted data efficiency to achieve a given target performance $J$. The budget-optimal UTD and model size are marked with stars. Comparing [BRO](https://arxiv.org/abs/2405.16158) and [SimbaV2](https://arxiv.org/abs/2502.15280) completes **Step 2**.

**Step 3:** Conveniently, our fit equation admits a closed-form solution for budget-optimal UTD and model size, in terms of the data efficiency! We find that, within a given budget, **UTD-only scaling and model-size–only scaling use 11% and 26% more data, respectively**, compared to the compute-optimal setting. In the paper, we similarly show that the data–compute partition is predictable at extrapolated budgets – check it out!

```markdown
Takeaways:

- Leveraging our understanding of TD-overfitting improves model size scaling.
- Data efficiency can be modeled as a sum of power laws decaying in UTD and model size.
- Our fits tell you whether it is more compute-efficient to scale your UTD or model size.
```

## A call for scalable RL algorithms

Scaling laws offer a blueprint for building reinforcement learning that scales. By identifying the scalable regime, we showed that value-based RL admits predictable scaling once its core instabilities, which manifest as overfitting, are resolved.

In supervised learning, scaling laws depend on the best choice of model size, batch size, and learning rate. In value-based RL, these relationships are much trickier to uncover, due to data distribution shift and the use of target networks in practice. These training dynamics are associated with a suite of parameters including the replay buffer size, optimizer, loss function (here distributional critic), and actor update frequency. Each new axis adds to the foundation for compute-optimal training, and in principle one could extend RL scaling law research to additional parameters and training regimes.

Ultimately, though, we must not only characterize existing methods, but also design better algorithms — ones that scale more reliably, across broader domains, and under more demanding budgets. The goal is not just to show that RL can scale, but to establish a general framework where scaling laws guide us toward the next generation of scalable RL algorithms.
