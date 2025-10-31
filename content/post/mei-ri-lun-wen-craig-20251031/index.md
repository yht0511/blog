---
title: "每日论文: craig #20251031"
description: ""
date: 2025-10-31T18:31:36+08:00
lastmod: 2025-10-31T18:31:36+08:00
categories: ["论文笔记"]
mermaid: true
draft: false
---
<span class="secret-placeholder" data-id="8e0894495b6de85b75ab49be2d960516a76b860a4b0e62ac62b73b3ddb31f4c3" title-hash="e6d66150a5caaa10e460768599d8bedbb8dd5418ae213fa0e9b09b3847c60adb"></span>

优化的几个实体: 参数 数据集 方法(loss、lr、正则)

目的: 在数据集上做精简,选子集来代表整体数据集,保证速度和精度的平衡.

原论文用一堆推导拿到了:

$$S^{*} = \arg \min_{S \subseteq V} |S|, \quad \text{s.t. } L(S) \triangleq \sum_{i \in V} \min_{j \in S} d_{ij} \le \epsilon (8)$$ 

意思就是,我对于所有数据点i, 找一个和他在梯度上最近似的j,然后计算这俩梯度差在所有参数上的最大值,然后所有i加起来就拿到最保守的估计, 这个估计要小于epsilon.

在这个上面可以证明Lipschitz连续性:

$$\forall w, i, j \quad \left\| \nabla f_i(w) - \nabla f_j(w) \right\| \le d_{ij} \le \text{const.} \cdot \|x_i - x_j\| (9)$$(我任何两个数据点对于任何参数的梯度最大值小于一个常数*这俩数据点的距离)

它的本质也比较简单,就是我选的数据集本身足够相似,那我最后的梯度影响也会相似,这里最关键的还是有界性.

> 子模性: 集合越大,我选一个点带来的收益越小.(边际收益递减)
>
> 显然loss函数是子模的.

因此可以一个个贪心地去选,时间复杂度O(r\*n^2), r是选的S点数,n是数据集大小.

![img](https://blog-cdn.yht.life/blog/202510311831663.png)

而这里贪婪算法提供了一个1-1/e的近似,这使得既可以保证精度去做,又可以按照资源限制去做.

> 证明: 因为最优解的剩余价值，小于等于最优解中所有未选元素在当前步的边际收益之和。那么我这一步的选择带来的边际效益至少大于等于最优解剩余价值的1/k(k为最优解中未选元素个数)。所以每一步都能保证至少获得1-1/k的最优解剩余价值。迭代k步后，最终结果至少是(1-1/e)的最优解。

深度神经网络不能直接用之前的(9),因为推导过程基于凸函数性质.

$$ \left\| \nabla f_i(w) - \nabla f_j(w) \right\| \le c_1 \left\| {\Sigma'}_{L}(z_i^{(L)}) \nabla f_i^{(L)}(w) - {\Sigma'}_{L}(z_j^{(L)}) \nabla f_j^{(L)}(w) \right\| + c_2 $$

这个的意思就是可以根据最后一层的梯度差来估计整体的梯度差.原理: 拿模型提取后的特征判断相似度.一边训练一边找代表性集合.训练过程中需要不断重新选择子集.

> 思考:会不会恶性循环导致分辨不出特征
>
> “For the classification problems, we separately select subsets from each class while maintaining the class ratios in the whole data, and apply IG to the union of the subsets. ”
>
> 原论文在分类任务上考虑了类别平衡的问题,每个类别单独选子集.