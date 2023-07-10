# pylint: disable =unused-wildcard-import
from ...core import *
# pylint: enable  =unused-wildcard-import
from .BasciHdsk import BasicHdsk






class DDec(Component):

    def __init__(self, node, pld_width, id_type='tgt'):
        super().__init__()
        self.node = node

        if id_type == 'tgt':    used_list = self.node.tgt_list
        else:                   used_list = self.node.src_list

        num = len(used_list)

        self.din = BasicHdsk(node.src_id_width, node.tgt_id_width, node.txn_id_width, pld_width).reverse()
        self.out_list = [self.create('out%s' % i, self.din.reverse()) for i in range(num)]

        # bin2onehot
        self.rdy_masked_list = []
        for i, dst in enumerate(used_list):
            id_hit_list = []
            for gid in dst.reachable_tgt_id_list:
                id_hit = self.create("id_hit_p%s_id%s" % (i,gid), Wire(UInt(1)))

                if id_type == 'tgt':    id_hit += Equal(self.din.tgt_id, UInt(node.tgt_id_width, gid))
                else:                   id_hit += Equal(self.din.src_id, UInt(node.src_id_width, gid))

                id_hit_list.append(id_hit)

            sel_bit = self.create("sel_bit%s" % i, Wire(UInt(1)))
            sel_bit += BitOrList(*id_hit_list)

            self.rdy_masked_list.append(And(sel_bit, self.out_list[i].rdy))
            
            vld = self.out_list[i].vld
            vld += And(sel_bit, self.din.vld)


        Assign(self.din.rdy, OrList(*self.rdy_masked_list))

        out_exclude_vld_rdy = [var.as_list(exclude=['rdy', 'vld']) for var in self.out_list]
        in_exlucde_vld_rdy = self.din.as_list(exclude=['rdy', 'vld'])

        for out_bundle in out_exclude_vld_rdy:
            for i, out_slice in enumerate(out_bundle):
                out_slice += in_exlucde_vld_rdy[i]

        



        # good
        #rdy = 
        #rdy += 

        # bad
        #self.din.rdy += OrList(*self.rdy_masked_list)

            # self.head_list[i]   += self.in0_head
            # self.tail_list[i]   += self.in0_tail
            # self.pld_list[i]    += self.in0_pld
            # self.mst_id_list[i] += self.in0_mst_id
            # self.slv_id_list[i] += self.in0_slv_id


        #for dst in self.node.dst_list:
        #    print(dst.global_id_list)

        #id_width = node.id_width

        # self.vld_list = []
        # self.rdy_list = []
        # self.head_list = []
        # self.tail_list = []
        # self.pld_list = []
        # self.mst_id_list = []
        # self.slv_id_list = []

        # for i in range(num):
        #     self.vld_list.append(self.create('out%s_vld' % i, Output(UInt(1))))
        #     self.rdy_list.append(self.create('out%s_rdy' % i, Input(UInt(1))))
        #     self.head_list.append(self.create('out%s_head' % i, Output(UInt(1))))
        #     self.tail_list.append(self.create('out%s_tail' % i, Output(UInt(1))))
        #     self.pld_list.append(self.create('out%s_pld' % i, Output(UInt(pld_width))))
        #     self.mst_id_list.append(self.create('out%s_id' % i, Output(UInt(master_id_width))))
        #     self.slv_id_list.append(self.create('out%s_id' % i, Output(UInt(slave_id_width))))



# class DDec2(Component):
# 
#     def __init__(self, node, pld_width, id_type='mst'):
#         super().__init__()
#         self.node = node
# 
#         if id_type == 'mst':    used_list = self.node.dst_list
#         else:                   used_list = self.node.src_list
# 
#         num = len(used_list)
# 
#         #pld_width        = node.network.pld_width
#         master_id_width  = node.tgt_id_width
#         slave_id_width   = node.src_id_width
# 
#         # Create Output
#         self.vld_list    = [self.create('out%s_vld'     % i, Output(UInt(1)))               for i in range(num)]
#         self.rdy_list    = [self.create('out%s_rdy'     % i, Input(UInt(1)))                for i in range(num)]
#         self.head_list   = [self.create('out%s_head'    % i, Output(UInt(1)))               for i in range(num)]
#         self.tail_list   = [self.create('out%s_tail'    % i, Output(UInt(1)))               for i in range(num)]
#         self.pld_list    = [self.create('out%s_pld'     % i, Output(UInt(pld_width)))       for i in range(num)]
#         self.mst_id_list = [self.create('out%s_mst_id'  % i, Output(UInt(master_id_width))) for i in range(num)]
#         self.slv_id_list = [self.create('out%s_slv_id'  % i, Output(UInt(slave_id_width)))  for i in range(num)]
# 
#         # Create Input
#         self.in0_vld     = Input(UInt(1))
#         self.in0_rdy     = Output(UInt(1))
#         self.in0_head    = Input(UInt(1))
#         self.in0_tail    = Input(UInt(1))
#         self.in0_pld     = Input(UInt(pld_width))
#         self.in0_mst_id  = Input(UInt(master_id_width))
#         self.in0_slv_id  = Input(UInt(slave_id_width))
# 
#         # bin2onehot
#         self.rdy_masked_list = []
#         for i, dst in enumerate(used_list):
#             id_hit_list = []
#             for gid in dst.global_master_id_list:
#                 id_hit = self.create("id_hit_p%s_id%s" % (i,gid), Wire(UInt(1)))
# 
#                 if id_type == 'mst':    id_hit += Equal(self.in0_mst_id, UInt(master_id_width, gid))
#                 else:                   id_hit += Equal(self.in0_mst_id, UInt(slave_id_width, gid))
# 
#                 id_hit_list.append(id_hit)
# 
#             sel_bit = self.create("sel_bit%s" % i, Wire(UInt(1)))
# 
#             if len(id_hit_list) < 2:
#                 sel_bit += id_hit_list[0]
#             else:
#                 sel_bit += BitOrList(*id_hit_list)
# 
#             self.rdy_masked_list.append(And(sel_bit, self.rdy_list[i]))
#             
#             self.vld_list[i] += And(sel_bit, self.in0_vld)
# 
#             self.head_list[i]   += self.in0_head
#             self.tail_list[i]   += self.in0_tail
#             self.pld_list[i]    += self.in0_pld
#             self.mst_id_list[i] += self.in0_mst_id
#             self.slv_id_list[i] += self.in0_slv_id
# 
# 
#         if len(self.rdy_masked_list) < 2:
#             self.in0_rdy += self.rdy_masked_list[0]
#         else:
#             self.in0_rdy += OrList(*self.rdy_masked_list)

