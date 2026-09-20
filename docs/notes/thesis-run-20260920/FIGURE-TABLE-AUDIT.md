# 图表复核

2026-09-20 实际调用现有 audit_thesis_figures.baseline()/verify()，将结果写本轮目录，未覆写2026-09-16旧工件。

17图16表编号连续、图题匹配、所有PNG/SVG/单图PDF存在、SVG无foreignObject、证据路径有效；原始截图SHA-256全部保持不变。10张结构表字段、类型、约束与Schema一致；36接口与权限表一致。结果见 current-figure-check.json。

图源JSON、manifest、fact-baseline、verification及README已读取。数据库无物理外键；知识点parent_id=0是根哨兵；practice_record的两个可空目标由服务端强制二选一；变式次数与每次数量有区分。图3.1保留角色与权限命名。未发现需重画的明确差异，未重建图源。

既有34页校样只作历史校样；本轮最终视觉检查随全文P06进行。Visio未注册/未实开，不生成虚假VSDX。截图仅作2026-08-26真实链路证据，后续图片识别功能不能借用这些截图证明。
