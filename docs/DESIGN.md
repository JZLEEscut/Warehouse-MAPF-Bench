# 设计与取舍 / Design decisions

## 数据流 / Data flow

```text
synthetic generator / Moving AI parser / diagnostic cases
                         |
                    MAPFProblem
                         |
        Independent A* / Prioritized Planning / CBS
                         |
                       Solution
                         |
                 independent validator
                         |
       raw CSV + paired analysis / JSON replay + browser
```

算法不依赖浏览器。交互页和实验共享求解器，且在展示或计入有效率前独立验证结果。页面只负责回放求解器返回的离散轨迹；动画不参与路径规划。完整但冲突的基线结果、失败后的部分路径、有效解有不同状态。

Solvers do not depend on the browser. The study and demo share solver implementations and independently validate outputs. Animation replays discrete paths; it does not compute them. Complete-but-conflicting baselines, partial failures and valid solutions have distinct states.

## 为什么增加静态 BFS / Why static BFS distances?

曼哈顿距离忽略障碍物。对无权四邻接栅格，从目标反向 BFS 可以得到所有可达格的静态最短距离。添加时间约束只可能增加或保持路径成本，因此该距离仍是 Space-Time A* 的可采纳下界；相邻自由格的距离差不超过 1，WAIT 也不破坏一致性。

每个目标表需要 O(V+E) 时间、O(V) 空间。DistanceCache 绑定一张不可变地图，且只存在于单次求解内：CBS 同一智能体在不同约束树节点重新规划时可以命中同一表，跨实验运行不复用。最坏情况下 k 个不同目标消耗 O(kV) 存储。约束、时间状态及路径没有被缓存。

Manhattan distance ignores obstacles. Reverse BFS gives exact static distances on an unweighted grid. Time constraints cannot shorten a route, so these distances remain admissible and consistent for Space-Time A*, including WAIT. Each table costs O(V+E) time and O(V) memory; a per-solve cache can use O(kV) memory across k goals. Constraints and paths are not cached.

缓存构建和查询使用求解器的同一个 deadline，超时的半成品不会进入缓存。计时从构建缓存之前开始；即使扩展数下降，预计算也可能导致总耗时上升。因此保留可切换的 Manhattan 基线及默认值，使用配对实验决定是否值得启用。

Preprocessing observes the shared deadline; partial tables are never cached. Its cost is charged to the solve. Fewer expansions can still mean slower execution, which is why Manhattan remains the default and both options are measured.

## 为什么增加优先级策略 / Why another priority order?

Prioritized Planning 按顺序预留路径和永久目标占用。在 goal_hold 案例中，A 只需一步到达路口，但停下后挡住 B 的通路；输入顺序无法找到方案。longest_first 用静态最短距离由长到短稳定排序，让 B 先通过路口，A 延迟到达目标。它是一个启发式，不提供完备性或全局最优保证，且可能使其他实例的 SOC 变差。

Prioritized Planning reserves paths and held goals in order. In goal_hold, parking A at the intersection first blocks B. Longest-first sorts by static shortest distance, preserving input order on ties; B crosses first and A delays its arrival. This heuristic is neither complete nor globally optimal and can worsen SOC elsewhere.

排序所需的 BFS 预计算也计入时间预算。同样的输入不会被原地重新排列，agent ID 和实验 instance ID 保持稳定。没有通过尝试多个顺序来额外获得预算。

Ordering preprocessing is charged to the budget, input agents are not mutated, and no extra attempts are hidden behind the strategy.

## 结果边界与验证 / Outcome boundaries and validation

CBS 根节点的单智能体搜索若失败，会在剩余预算内检查静态可达性。静态不可达时报告 no_solution；静态可达但指定 horizon 不够时报告 no_solution_within_limits；诊断 BFS 本身超时时仍报告 timeout。有限搜索失败不能自动证明全局不可解。

Space-Time A* 也必须尊重到达目标之后的约束：目标点在未来被禁止占用时，不能提前结束；未来禁止目标到自身的 WAIT 边时，也不能返回会永久停留在该目标上的路径。这两个边界都有回归测试。

When a root search fails, CBS checks static reachability within the remaining budget. Static disconnection is no_solution; a reachable goal beyond the horizon is no_solution_within_limits; diagnostic preprocessing can itself time out. Future goal occupancy and goal-to-itself WAIT edge constraints must both be respected before accepting a held-goal path.

## 为什么只做轻量本地页面 / Why a small local UI?

页面用原生 HTML/SVG 回放轨迹，后端用标准库 HTTP 服务，复用现有依赖。每次求解使用新缓存，CBS 与 Prioritized 在页面上均限制为 2 秒，车辆最多 25 台；服务一次只接受一个求解请求，忙时返回 429。没有账号、数据库或部署服务，保持重点在规划和实验。

The local UI uses native HTML/SVG and the standard-library HTTP server. Each solve has a fresh cache, a two-second CBS/Prioritized budget and a 25-agent cap. Concurrent solve requests receive 429. Keeping the interface small leaves the focus on planning and measurement.

## 验证证据 / Verification

- 随机小地图上，将反向 BFS 与独立正向 BFS 对比，检查可达性和距离。
- 同一约束下比较两种启发式的最短路成本；检查已知最优 CBS 案例。
- 用注入时钟检查预计算超时，确保半成品表不会复用。
- 检查短 horizon、静态不可达、永久目标占用和未来 WAIT 约束。
- 真实 HTTP 测试覆盖页面资源、JSON、非法参数、未知路由及服务忙状态。
- 检查重复实验的配对次数与独立实例数，防止将重复计时当成扩大样本。

Tests cover randomized distance-oracle comparisons, constrained shortest costs, known CBS optima, deadline interruption, cutoff semantics, held goals, real HTTP responses and correct repetition pairing. Timing results and limitations are documented in EXPERIMENTS.md.
