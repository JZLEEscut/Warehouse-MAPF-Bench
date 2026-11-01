# 项目讲解 / Interview walkthrough

## 一分钟介绍 / One-minute introduction

这个项目研究仓储栅格地图中多台 AGV 如何同时到达目标而不碰撞。我实现了独立 A*、时空 A*、优先级规划和 CBS，并把算法输出交给独立验证器，检查顶点冲突、交换冲突以及到达后的目标持续占用。

工程上，我增加了可单步回放的本地演示和可复现的实验。一次具体改进是用按目标缓存的反向 BFS 距离替代曼哈顿启发式，并将预计算也计入 deadline 和运行时间。实验区分全部尝试和共同有效实例，也分别报告重复次数与独立实例数，所以可以讨论搜索工作量、实际耗时和质量之间的取舍。

The project studies collision-free routing for warehouse AGVs on a discrete grid. It implements independent A*, Space-Time A*, Prioritized Planning and CBS, with independent validation of moves, conflicts and held goals. A local replay UI makes behaviors inspectable. A measured reverse-BFS heuristic ablation includes preprocessing costs and separates all attempts, paired-valid quality, repeated timings and unique instances.

## 五分钟演示 / Five-minute demonstration

1. 启动 `python -m warehouse_mapf.web_demo`，打开本机 8765 端口。
2. 选择 crossing + Independent A*。拖动时间轴到 t=1，解释红圈顶点冲突；完整返回路径仍不代表有效解。
3. 切换 CBS，在相同场景单步回放，解释 WAIT 如何消除冲突，以及 SOC=5 的已知最优例子。
4. 选择 goal_hold + Prioritized Static。解释 A 停在路口后，B 无法通过；失败时展示的部分路径不是完整方案。
5. 切换 Prioritized Longest first + BFS。说明排序改变了预留顺序，B 先通过，A 再停入目标。
6. 展示 `benchmarks/v0_3_improvements/paired_summary.csv`，说明实际数据是否支持速度或质量改进，以及适用范围。

Demo sequence: show the independent conflict, resolve it with CBS, reproduce the held-goal priority failure, fix that instance with longest-first, then inspect the recorded ablation rather than generalizing from a single animation.

## 可以深入讨论的问题 / Technical discussion

| 问题 / Question | 结合代码说明 / Evidence to discuss |
| --- | --- |
| 为什么要时空搜索？ / Why search in time? | 同一个格子在不同时间是不同状态；WAIT 是合法动作。 |
| BFS 距离为何可采纳？ / Why is BFS admissible? | 静态最短路忽略时间约束，提供带约束成本的下界。 |
| 减少扩展为何未必更快？ / Why can fewer expansions be slower? | 预计算、缓存字典操作、约束预留和冲突检测都有成本；以配对表和总耗时回答。 |
| CBS 的代价来自哪里？ / Where does CBS spend work? | 高层对冲突分支，低层重复规划；区分两层扩展数，超时保留全部尝试记录。 |
| 为什么排序不能保证解？ / Why is ordering incomplete? | 固定高优先级轨迹可能封死后续路线，corridor 案例需要较早路径主动避让。 |
| 如何判断不可解？ / How is impossibility reported? | 静态不连通可以证明某个智能体不可达；有限 horizon 或搜索资源耗尽不能证明全局不可解。 |
| 如何保证实验公平？ / How are comparisons controlled? | 相同实例与预算、冷缓存、确定性打乱顺序、重复计时、配对有效质量、环境与源码哈希。 |

## 简历可用表述 / Resume wording

实现仓储多智能体路径规划实验框架，覆盖 A*、Space-Time A*、Prioritized Planning 与 CBS；构建独立碰撞验证、配对基准和交互式轨迹回放，完成静态距离缓存与优先级策略的消融实验，并修复搜索时域导致的结果误分类。

Implemented a warehouse MAPF benchmark with A*, Space-Time A*, Prioritized Planning and CBS; added independent collision validation, paired analysis and interactive replay; evaluated cached static-distance heuristics and priority ordering, and corrected finite-horizon outcome classification.

量化结果引用随仓库提交的原始数据。这里不预填“性能提升百分比”，也不把三次计时重复当成三个独立问题实例。

Use the committed data for quantitative claims; three timing repetitions are not three distinct planning instances.
