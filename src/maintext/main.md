code 1 may need a big refactor :P, code 2 is mostly working

would be nice to combine the two repos (?)

Modern machine learning has seen dramatic gains simply by scaling up models, data, and compute following simple [power laws](https://arxiv.org/abs/2001.08361). In supervised learning, these laws predict how loss decreases as you enlarge your model or dataset, enabling practitioners to find the [compute-optimal](https://arxiv.org/abs/2203.15556) model size for a given budget without costly hyperparameter searches.

On-policy RL methods, like PPO and GRPO, have likewise leveraged scaling to achieve impressive results in simulated environments and language models, but they require fresh training example after every policy update. This limits their sample efficiency in settings where data collection is slow or expensive (e.g. robotics).

By contrast, **off-policy RL** methods, can in principle learn from any data, regardless of how it was collected. In particular, they can train on the same data multiple times, dramatically boosting sample efficiency by decoupling data collection from policy updates. This capability is essential when each trial costs minutes of wall-clock time or risks hardware damage. However, this strength introduces new challenges for scaling:

- **Two resource axes:** RL training hinges on both the **amount of environment data** $\mathcal D$ and the **compute** $\mathcal C$ (FLOPs) spent updating on that data.
- **Non-stationary data:** As agents update their policy $\pi$, the distribution of collected experiences shifts, unlike the static datasets of supervised learning.
- **Moving targets:** Q-functions $Q_\theta$ regress onto bootstrapped targets $\bar Q$ that change over the course of training, adding instability.

We challenge the conventional wisdom that RL’s bootstrapping and non-stationarity hinders predictability. [add prior work section plus a clear distinction between online and offline]

:::jumpbox id="utd_scaling":::

## A mechanistic understanding, Take 1: How should I set my batch size and learning rate?

Scaling laws for supervised learning [rely](https://arxiv.org/abs/2203.15556) on [reasonable estimates](https://arxiv.org/abs/1404.5997) for the best [batch size](https://arxiv.org/abs/1812.06162) and [learning rate](https://arxiv.org/abs/2203.03466) for each configuration. [insert some more info on why this is important]

Off-policy algorithms minimize the temporal difference (TD) error

$$L(\theta) = \mathbb{E}_{(s, a, s') \sim \mathcal{P}, a' \sim \pi(\cdot|s')}\left[ \left(r(s, a) + \gamma \bar{Q}(s', a') - Q_\theta(s, a) \right)^2\right]$$

where each gradient step samples a batch of transitions from the replay buffer $\mathcal P$. We can make them sample-efficient by taking multiple gradient steps on the same batch, known as the **updates-to-data (UTD) ratio** $\sigma$. Increasing the UTD ratio tends to improve performance for small $\sigma$, but we show that pushing the UTD ratio further tends to overfit to stale data on old targets $\bar Q$ and generalize poorly to newly collected data. Therefore, doing so naively can [eventually worsen](https://arxiv.org/abs/2205.07802) performance.

In fact, we observe that training with large batch sizes has a similar effect: we see the average sample more times and overfit to those samples, resulting in worse TD error on data recently collected by the policy $\pi$. **To counteract this effect at high UTD ratios, we reduce the batch size $B$.** Empirically, we find that this inverse rule can be approximated as a power law: $B^*(\sigma) \propto \sigma^{-\alpha_B}$.

![image.png](/assets/images/model_scaling_temp.png "above is a sample image, this is a sample caption"){width=400px}

![image.png](attachment:9255258b-8cfd-4b65-a9fa-50f7cb3af546:image.png)

We also observe that high UTD ratios lead to plasticity loss, i.e. the inability to fit TD targets appearing later in training, as diagnosed by large parameter norm in the Q-network in [prior work](https://openreview.net/forum?id=OpC-9aBBVJe). Similarly, we hypothesize that higher learning rates lead to high-magnitude updates against the target, moving the parameters to a state that would suffer from difficulty in fitting subsequent targets. Empirically, we find that **larger UTD ratios need smaller learning rates** $\eta$, as approximated by a power law: $\eta^*(\sigma) \propto \sigma^{-\alpha_\eta}$.

![image.png](attachment:bb7379d4-d7f6-4884-a26f-4cc458373649:image.png)

![image.png](attachment:49e541e6-872e-407a-b762-51d57527036f:image.png)

## Data and compute requirements are traded off by the updates-to-data ratio

Armed with the best-choice batch size and learning rate, we can measure the **data efficiency**, i.e. the amount of data $\mathcal D_J$ needed to attain a target level of performance $J$ on a given environment. We find that **data efficiency scales as a power law with respect to $\sigma$**,

$\mathcal{D}_J(\sigma) \approx \mathcal{D}^{\mathrm{min}}_J + \left(\frac{\beta_J}{\sigma}\right)^{\alpha_J}$

across multiple domains, tasks, and algorithms.

![image.png](attachment:7e4eb55e-9f80-4de1-a312-5fc2cc4801ea:662cbc9c-2a68-4a96-8b7c-c1263c20b055.png)

We can similarly define the amount of compute $\mathcal C_J(\sigma)$, measured in FLOPs, required to attain performance threshold $J$. Notably, for each $J$, the UTD ratio $\sigma$ defines a Pareto frontier $(\mathcal D_J(\sigma), \mathcal C_J(\sigma))$ between data and compute requirements.

Typically, we’d like to strike a balance between these requirements and define a budget function $\mathcal F = \mathcal C + \delta \cdot \mathcal D$ for a constant $\delta$. An example budget function is wall clock time; in this case, we’d set $\delta$ as the ratio between our GPU’s `FLOPs per second` to our environment’s `env steps per second`. We use this choice of $\delta$ and numerically compute the optimal $(\mathcal D_J^*, \mathcal C_J^*)$ for each threshold with corresponding budget $\mathcal F_J^*$ and UTD ratio $\sigma^*(\mathcal F_J^*)$. We observe **a power law relation between $\mathcal F_J^*$ and $\sigma^*(\mathcal F_J^*)$:** $\sigma^*(\mathcal{F}_J^*) \propto (\mathcal F_J^*)^{-\alpha_\sigma}$ and verify that it extrapolates well to higher budgets!

![image.png](attachment:85ff0d06-f345-4c62-9d32-265daa957c30:image.png)

:::jumpbox id="model_scaling":::

![image.png](attachment:f56eecb7-d721-4bfb-b5a8-42cd896a6904:0aa2ba64-e273-40fc-bd33-85f3778efcde.png)

## A mechanistic understanding, Take 2: TD-overfitting

## Partitioning compute optimally between model size and UTD

insert
