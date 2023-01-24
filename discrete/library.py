import copy
from functools import reduce
from operator import add
from itertools import permutations
from numpy import inf
import numpy as np

from commons.library import *

dim_to_let = {0: 'x', 1: 'y', 2: 'z'}


# as usual: this version of the code will not solve the general problem of observables with rank>2 
class CoarseGrainedPrimitive(object):  # represents rho[product of obs_list]
    def __init__(self, obs_list):  # obs_list should be sorted to maintain canonical order
        self.obs_list = obs_list
        self.obs_ranks = [obs.rank for obs in obs_list]  # don't know if we'll need this
        self.rank = sum(self.obs_ranks)
        # add 1 for the coarse-graining operator, rho[1] counts for 1.33
        self.complexity = (len(obs_list) if obs_list != [] else 0.33) + 1

    def __repr__(self):
        repstr = [str(obs) + ' * ' for obs in self.obs_list]
        return f"rho[{reduce(add, repstr)[:-3]}]" if repstr != [] else "rho"

    def __hash__(self):  # it's nice to be able to use CGP in sets or dicts
        return hash(self.__repr__())

    def index_str(self, obs_dims, coord=False):
        indexed_str = ""
        dim_ind = 0
        for obs, rank in zip(self.obs_list, self.obs_ranks):
            if rank == 0:
                indexed_str += str(obs) + ' * '
            else:
                if coord:  # x/y/z
                    let = dim_to_let[obs_dims[dim_ind]]
                else:  # i/j/k
                    let = num_to_let_dict[obs_dims[dim_ind]]
                indexed_str += f"{str(obs)}_{let} * "
                dim_ind += 1
        # for obs, dims in zip(self.obs_list, obs_dims):
        #    if len(dims) == 0:
        #        indexed_str += str(obs) + ' * '
        #    else:
        #        let = dim_to_let[dim[0]]
        #        indexed_str += f"{str(obs)}_{let} * "
        return f"rho[{indexed_str[:-3]}]" if indexed_str != "" else "rho"

    def __lt__(self, other):
        if not isinstance(other, CoarseGrainedPrimitive):
            raise TypeError("Second argument is not a CoarseGrainedPrimitive.")
        for a, b in zip(self.obs_list, other.obs_list):
            if a == b:
                continue
            else:
                return a < b
        return len(self.obs_list) < len(other.obs_list)

    # TODO: This may be redundant. I believe python does this proccess internally.
    def __gt__(self, other):
        if not isinstance(other, CoarseGrainedPrimitive):
            raise TypeError("Second argument is not a CoarseGrainedPrimitive.")
        return other.__lt__(self)

    def __eq__(self, other):
        if not isinstance(other, CoarseGrainedPrimitive):
            raise TypeError("Second argument is not a CoarseGrainedPrimitive.")
        return self.obs_list == other.obs_list

    def __ne__(self, other):
        return not self.__eq__(other)

    # def __mul__(self, other):
    #    if isinstance(other, CoarseGrainedPrimitive):
    #        return CoarseGrainedPrimitive(self.obs_list + other.obs_list)
    #    else:
    #        raise TypeError(f"Cannot multiply {type(self)}, {type(other)}")

    def index_canon(self, inds):
        if len(inds) == 0:
            return inds
        new_inds = copy.deepcopy(inds)
        reps = 1
        prev = self.obs_list[0]
        obs_start_ind = 0
        ind_start_ind = 0
        while obs_start_ind < len(self.obs_list) - 1:
            prev = self.obs_list[obs_start_ind]
            while obs_start_ind + reps < len(self.obs_list) and prev == self.obs_list[reps]:
                reps += 1
            if prev.rank > 0:
                new_inds[ind_start_ind:ind_start_ind + reps] = sorted(new_inds[ind_start_ind:ind_start_ind + reps])
            obs_start_ind += reps
            ind_start_ind += reps * prev.rank
        return new_inds

    def is_index_canon(self, inds):  # can just check that inds == index_canon(ind), but this is more efficient
        # print(self.obs_list)
        # print(inds)
        if len(inds) == 0:
            return inds
        reps = 1
        prev = self.obs_list[0]
        obs_start_ind = 0
        ind_start_ind = 0
        while obs_start_ind < len(self.obs_list) - 1:
            prev = self.obs_list[obs_start_ind]
            while obs_start_ind + reps < len(self.obs_list) and prev == self.obs_list[reps]:
                reps += 1
            ni = inds[ind_start_ind:ind_start_ind + reps]
            if prev.rank == 0 or all(a <= b for a, b in zip(ni, ni[1:])):
                obs_start_ind += reps
                ind_start_ind += reps * prev.rank
            else:
                # print('false')
                return False
        # print('true')
        return True


# noinspection PyArgumentList
@dataclass
class LibraryPrimitive(object):
    dorder: DerivativeOrder
    cgp: CoarseGrainedPrimitive
    rank: int = field(init=False)
    complexity: int = field(init=False)

    def __post_init__(self):
        self.rank = self.dorder.xorder + self.cgp.rank
        self.complexity = self.dorder.complexity + self.cgp.complexity

    def __repr__(self):
        tstring, xstring = create_derivative_string(self.dorder.torder, self.dorder.xorder)
        return f'{tstring}{xstring}{self.cgp}'

    def __hash__(self):
        return hash(self.__repr__())

    # For sorting: convention is (1) in ascending order of name, (2) in *ascending* order of dorder

    def __lt__(self, other):
        if not isinstance(other, LibraryPrimitive):
            raise TypeError("Second argument is not a LibraryPrimitive.")
        if self.cgp == other.cgp:
            return self.dorder < other.dorder
        else:
            return self.cgp < other.cgp

    def __gt__(self, other):
        if not isinstance(other, LibraryPrimitive):
            raise TypeError("Second argument is not a LibraryPrimitive.")
        return other.__lt__(self)

    def __eq__(self, other):
        if not isinstance(other, LibraryPrimitive):
            raise TypeError("Second argument is not a LibraryPrimitive.")
        return self.cgp == other.cgp and self.dorder == other.dorder

    def __ne__(self, other):
        return not self.__eq__(other)

    def dt(self):
        return LibraryPrimitive(self.dorder.dt(), self.cgp)

    def dx(self):
        return LibraryPrimitive(self.dorder.dx(), self.cgp)


# (1) Evaluation will need some rework to account for repetitions both within derivatives and coarse-grained primitive
class IndexedPrimitive(LibraryPrimitive):
    def __init__(self, prim, space_orders=None, obs_dims=None, newords=None):
        # obs_dims should be a flat list
        # however, it will be converted tо nested list where inner lists correspond to indices of observable
        self.dorder = prim.dorder
        self.cgp = prim.cgp
        self.rank = prim.rank
        self.complexity = prim.complexity
        if newords is None:  # normal constructor
            self.dimorders = space_orders + [self.dorder.torder]
            self.obs_dims = obs_dims
        else:  # modifying constructor
            self.dimorders = newords
            self.obs_dims = prim.obs_dims
        self.ndims = len(self.dimorders)
        self.nderivs = sum(self.dimorders)

    def __repr__(self):
        torder = self.dimorders[-1]
        xstring = ""
        for i in range(len(self.dimorders) - 1):
            let = dim_to_let[i]
            xorder = self.dimorders[i]
            if xorder == 0:
                xstring += ""
            elif xorder == 1:
                xstring += f"d{let} "
            else:
                xstring += f"d{let}^{xorder} "
        if torder == 0:
            tstring = ""
        elif torder == 1:
            tstring = "dt "
        else:
            tstring = f"dt^{torder} "
        return f'{tstring}{xstring}{self.cgp.index_str(self.obs_dims, coord=True)}'

    def __eq__(self, other):
        return (self.dimorders == other.dimorders and self.cgp == other.cgp
                and self.obs_dims == other.obs_dims)

    def succeeds(self, other, dim):
        copyorders = copy.deepcopy(self.dimorders)
        copyorders[dim] += 1
        return copyorders == other.dimorders and self.cgp == other.cgp and self.obs_dims == other.obs_dims

    def diff(self, dim):
        newords = copy.deepcopy(self.dimorders)
        newords[dim] += 1
        return IndexedPrimitive(self, newords=newords)

    def __mul__(self, other):
        if isinstance(other, IndexedTerm):
            return IndexedTerm(obs_list=[self] + other.obs_list)
        else:
            return IndexedTerm(obs_list=[self] + [other])


class LibraryTensor(object):  # unindexed version of LibraryTerm
    def __init__(self, observables):
        if isinstance(observables,
                      LibraryPrimitive):  # constructor for library terms consisting of a primitive w/ some derivatives
            self.obs_list = [observables]
        else:  # constructor for library terms consisting of a product
            self.obs_list = observables
        self.rank = sum([obs.rank for obs in self.obs_list])
        self.complexity = sum([obs.complexity for obs in self.obs_list])

    def __mul__(self, other):
        if isinstance(other, LibraryTensor):
            return LibraryTensor(self.obs_list + other.obs_list)
        elif other == 1:
            return self
        else:
            raise TypeError(f"Cannot multiply {type(self)}, {type(other)}")

    def __rmul__(self, other):
        if other != 1:
            return other.__mul__(self)
        else:
            return self

    def __repr__(self):
        repstr = [str(obs) + ' * ' for obs in self.obs_list]
        return reduce(add, repstr)[:-3]


def labels_to_ordered_index_list(labels, ks):
    n = len(ks)
    index_list = [[None] * ks[i] for i in range(n)]
    for key in sorted(labels.keys()):
        for a, b in labels[key]:
            index_list[a][b] = key
    return index_list


def ordered_index_list_to_labels(index_list):
    labels = dict()
    for i, li in enumerate(index_list):
        for j, ind in enumerate(li):
            if ind in labels.keys():
                labels[ind].append((i, j))
            else:
                labels[ind] = [(i, j)]
    return labels


# each label maps to [(bin1, order1), (bin2, order2)], treat sublists of index_list as ordered.
# note: be careful not to modify index_list or labels without remaking because the references are reused
class LibraryTerm(object):
    canon_dict = dict()  # used to store ambiguous canonicalizations (which shouldn't exist for less than 6 indices)

    def __init__(self, libtensor, labels=None, index_list=None):
        self.obs_list = libtensor.obs_list
        self.bin_sizes = flatten([(observable.dorder.xorder, observable.cgp.rank)
                                  for observable in self.obs_list])
        self.libtensor = libtensor
        self.rank = (libtensor.rank % 2)
        self.complexity = libtensor.complexity
        if labels is not None:  # from labels constructor
            self.labels = labels  # dictionary: key = index #, value(s) = location of index among 2n bins
            self.index_list = labels_to_ordered_index_list(labels, self.bin_sizes)
        else:  # from index_list constructor
            self.index_list = index_list
            self.labels = ordered_index_list_to_labels(index_list)
        self.der_index_list = self.index_list[0::2]
        self.obs_index_list = self.index_list[1::2]
        self.is_canonical = None

    def __add__(self, other):
        if isinstance(other, LibraryTerm):
            return TermSum([self, other])
        else:
            return TermSum([self] + other.term_list)

    def __eq__(self, other):
        if isinstance(other, LibraryTerm):
            return self.obs_list == other.obs_list and self.index_list == other.index_list
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return str(self) < str(other)

    def __gt__(self, other):
        return str(self) > str(other)

    def __repr__(self):
        repstr = [label_repr(obs, ind1, ind2) + ' * ' for (obs, ind1, ind2) in
                  zip(self.obs_list, self.der_index_list, self.obs_index_list)]
        return reduce(add, repstr)[:-3]

    def __hash__(self):  # it's nice to be able to use LibraryTerms in sets or dicts
        return hash(self.__repr__())

    def __mul__(self, other):
        if isinstance(other, LibraryTerm):
            if self.rank < other.rank:
                return other.__mul__(self)
            if len(self.labels.keys()) > 0:
                shift = max(self.labels.keys())
            else:
                shift = 0
            if other.rank == 1:
                a, b = self.increment_indices(1), other.increment_indices(shift + 1)
            else:
                a, b = self, other.increment_indices(shift)
            return LibraryTerm(LibraryTensor(a.obs_list + b.obs_list),
                               index_list=a.index_list + b.index_list).canonicalize()
        elif str(other) == "1":
            return self
        elif isinstance(other, Equation):
            return other.__mul__(self)
        else:
            raise TypeError(f"Cannot multiply {type(self)}, {type(other)}")

    def __rmul__(self, other):
        return self.__mul__(other)

    def structure_canonicalize(self):
        indexed_zip = zip(self.obs_list, self.der_index_list, self.obs_index_list)
        sorted_zip = sorted(indexed_zip, key=lambda x: x[0])
        if sorted_zip == indexed_zip:  # no changes necessary
            return self
        sorted_obs = [e[0] for e in sorted_zip]
        sorted_ind1 = [e[1] for e in sorted_zip]
        sorted_ind2 = [e[2] for e in sorted_zip]
        sorted_ind = flatten(zip(sorted_ind1, sorted_ind2))
        sorted_libtens = LibraryTensor(sorted_obs)
        return LibraryTerm(sorted_libtens, index_list=sorted_ind)

    # noinspection PyUnusedLocal
    def index_canonicalize(self):
        # inc = 0
        # if len(self.labels[0])==2: # if multiple i's, need to increment all indices
        #    inc = 1
        subs_dict = canonicalize_indices(flatten(self.index_list))
        # (a) do index substitutions, (b) sort within sublists 
        new_index_list = [[subs_dict[i] for i in li] for li in self.index_list]
        for li in new_index_list[::2]:  # sort all derivative indices
            li = sorted(li)
        for obs, li in zip(self.obs_list, new_index_list[1::2]):  # canonicalize CGPs
            li = obs.cgp.index_canon(li)
        if all([li1 == li2 for li1, li2 in zip(self.index_list, new_index_list)]):  # no changes were made
            return self
        return LibraryTerm(self.libtensor, index_list=new_index_list)

    def reorder(self, template):
        indexed_zip = zip(self.obs_list, self.der_index_list, self.obs_index_list, template)
        sorted_zip = sorted(indexed_zip, key=lambda x: x[3])
        sorted_obs = [e[0] for e in sorted_zip]
        sorted_ind1 = [e[1] for e in sorted_zip]
        sorted_ind2 = [e[2] for e in sorted_zip]
        sorted_ind = flatten(zip(sorted_ind1, sorted_ind2))
        sorted_libtens = LibraryTensor(sorted_obs)
        return LibraryTerm(sorted_libtens, index_list=sorted_ind)

    def canonicalize(self):  # return canonical representation and set is_canonical flag (used to determine if valid)
        str_canon = self.structure_canonicalize()
        if str_canon in self.canon_dict:
            canon = self.canon_dict[str_canon]
            self.is_canonical = (self == canon)
            return canon
        reorderings = []
        alternative_canons = []
        for template in get_isomorphic_terms(str_canon.obs_list):
            term = str_canon.reorder(template)
            if term not in reorderings:  # exclude permutation-symmetric options
                reorderings.append(term)
                canon_term = term.index_canonicalize()
                alternative_canons.append(canon_term)
        canon = min(alternative_canons, key=str)
        for alt_canon in alternative_canons:
            self.canon_dict[alt_canon] = canon
            self.is_canonical = (self == canon)
        return canon

    def increment_indices(self, inc):
        index_list = [[index + inc for index in li] for li in self.index_list]
        return LibraryTerm(LibraryTensor(self.obs_list), index_list=index_list)

    def dt(self):
        terms = []
        for i, obs in enumerate(self.obs_list):
            new_obs = obs.dt()
            # note: no need to recanonicalize terms after a dt
            lt = LibraryTerm(LibraryTensor(self.obs_list[:i] + [new_obs] + self.obs_list[i + 1:]),
                             index_list=self.index_list)
            terms.append(lt)
        ts = TermSum(terms)
        return ts.canonicalize()

    def dx(self):
        terms = []
        for i, obs in enumerate(self.obs_list):
            new_obs = obs.dx()
            new_index_list = copy.deepcopy(self.index_list)
            new_index_list[2 * i].insert(0, 0)
            lt = LibraryTerm(LibraryTensor(self.obs_list[:i] + [new_obs] + self.obs_list[i + 1:]),
                             index_list=new_index_list)
            if lt.rank == 0:
                lt = lt.increment_indices(1)
            lt = lt.canonicalize()  # structure changes after derivative so we must recanonicalize
            terms.append(lt)
        ts = TermSum(terms)
        # print(self.obs_list, "->", [term.obs_list for term in ts.term_list])
        # print(self.index_list, "->", [term.index_list for term in ts.term_list])
        return ts.canonicalize()


class IndexedTerm(object):  # LibraryTerm with i's mapped to x/y/z
    def __init__(self, libterm=None, space_orders=None, nested_obs_dims=None, obs_list=None):
        if obs_list is None:  # normal "from scratch" constructor
            self.rank = libterm.rank
            self.complexity = libterm.complexity
            nterms = len(libterm.obs_list)
            self.obs_list = copy.deepcopy(libterm.obs_list)
            for i, obs, sp_ord, obs_dims in zip(range(nterms), libterm.obs_list, space_orders, nested_obs_dims):
                self.obs_list[i] = IndexedPrimitive(obs, sp_ord, obs_dims)
            self.ndims = len(space_orders[0]) + 1
            self.nderivs = np.max([p.nderivs for p in self.obs_list])
        else:  # direct constructor from observable list
            # print(obs_list)
            if len(obs_list) > 0:  # if term is not simply equal to 1
                self.rank = obs_list[0].rank
                self.ndims = obs_list[0].ndims
                self.obs_list = obs_list
                self.complexity = sum([obs.complexity for obs in obs_list])
                self.nderivs = np.max([p.nderivs for p in self.obs_list])
            else:
                self.obs_list = []
                self.ndims = 0
                self.nderivs = 0
                self.complexity = 0

    def __repr__(self):
        repstr = [str(obs) + ' * ' for obs in self.obs_list]
        return reduce(add, repstr)[:-3]

    def __mul__(self, other):
        if isinstance(other, IndexedTerm):
            return IndexedTerm(obs_list=self.obs_list + other.obs_list)
        else:
            return IndexedTerm(obs_list=self.obs_list + [other])

    def drop(self, obs):  # remove one instance of obs
        obs_list_copy = copy.deepcopy(self.obs_list)
        if len(obs_list_copy) > 1:
            obs_list_copy.remove(obs)
        else:
            obs_list_copy = []
        return IndexedTerm(obs_list=obs_list_copy)

    def drop_all(self, obs):  # remove *aLL* instances of obs
        if len(self.obs_list) > 1:
            obs_list_copy = list(filter(obs.__ne__, self.obs_list))
        else:
            obs_list_copy = []
        return IndexedTerm(obs_list=obs_list_copy)

    def diff(self, dim):
        for i, obs in enumerate(self.obs_list):
            yield obs.diff(dim) * self.drop(obs)


# Note: must be handled separately in derivatives
class ConstantTerm(IndexedTerm):
    def __init__(self):
        self.obs_list = []
        self.rank = 0
        self.complexity = 0
        self.is_canonical = True

    def __repr__(self):
        return "1"

    def canonicalize(self):
        return self

    def __mul__(self, other):
        return other

    def __rmul__(self, other):
        return other

    @staticmethod
    def dt():
        return None

    @staticmethod
    def dx():
        return None


def label_repr(prim, ind1, ind2):
    torder = prim.dorder.torder
    xorder = prim.dorder.xorder
    cgp = prim.cgp
    if torder == 0:
        tstring = ""
    elif torder == 1:
        tstring = "dt "
    else:
        tstring = f"dt^{torder} "
    if xorder == 0:
        xstring = ""
    else:
        ind1 = [num_to_let_dict[i] for i in ind1]
        ind1 = compress(ind1)
        xlist = [f"d{letter} " for letter in ind1]
        xstring = reduce(add, xlist)
    return tstring + xstring + cgp.index_str(ind2)


def yield_tuples_up_to(bounds):
    if len(bounds) == 0:
        yield ()
        return
    for i in range(bounds[0] + 1):
        for tup in yield_tuples_up_to(bounds[1:]):
            # print(i, tup)
            yield (i,) + tup


def yield_legal_tuples(bounds):
    # print("bounds:", bounds)
    if sum(bounds[:-2]) > 0:  # if there are still other observables left
        # print("ORDERS:", bounds)
        yield from yield_tuples_up_to(bounds)
    else:  # must return all derivatives immediately
        # print("Dump ORDERS")
        yield bounds


# (4) SIGNIFICANT CHANGES
# check!
# def raw_library_tensors(observables, obs_orders, nt, nx, max_order=None, zeroidx=0):
def raw_library_tensors(observables, orders, max_order=None, zeroidx=0):
    # basically: iteratively take any possible subset from [obs_orders; nrho; nt; nx] 
    # as long as it's lexicographically less than previous order; take at least one of first observable

    # print(orders, max_order, zeroidx)
    n = len(observables)
    if orders[n] == 0:
        if sum(orders) > 0:  # invalid distribution
            return
        else:
            yield 1
            return
    while zeroidx < n and orders[zeroidx] == 0:
        zeroidx += 1
    if zeroidx < n:
        orders[zeroidx] -= 1  # always put in at least one of these to maintain lexicographic order

    # orders = obs_orders + [nt, nx]
    # print("ORDERS: ", orders)
    for tup in yield_legal_tuples(orders[:n] + [0] + orders[n + 1:]):  # ignore the rho index
        orders_copy = orders.copy()
        popped_orders = list(tup)
        # print("Popped: ", popped_orders)
        for i in range(len(orders)):
            orders_copy[i] -= popped_orders[i]
        if sum(orders_copy[:-2]) == 0 and sum(
                orders_copy[-2:]) > 0:  # all observables + rho popped but derivatives remain
            continue  # otherwise we will have duplicates from omitting derivatives
        if zeroidx < n:
            popped_orders[zeroidx] += 1  # re-adding the one
        orders_copy[n] -= 1  # account for the rho we used
        popped_orders[n] += 1  # include the rho here as well
        po_cl = CompList(popped_orders)
        if max_order is None or po_cl <= max_order:
            obs_list = []
            for i, order in enumerate(popped_orders[:-3]):  # rho appears automatically so stop at -3
                obs_list += [observables[i]] * order
            cgp = CoarseGrainedPrimitive(obs_list[::-1])  # flip order of observables back to ascending
            do = DerivativeOrder(popped_orders[-2], popped_orders[-1])
            prim = LibraryPrimitive(do, cgp)
            term1 = LibraryTensor(prim)
            # for term2 in raw_library_tensors(observables, orders[:-2], orders[-2], orders[-1], max_order=max_order):
            for term2 in raw_library_tensors(observables, orders_copy, po_cl, zeroidx):
                yield term2 * term1  # reverse order here to match canonicalization rules!


rho = Observable('rho', 0)
v = Observable('v', 1)


def generate_terms_to(order, observables=None, max_observables=999, max_rho=999):
    # note: this ignores the fact that rho operator adds complexity, but you can filter by complexity later
    if observables is None:
        observables = [rho, v]
    observables = sorted(observables, reverse=True)  # ordering opposite of canonicalization rules for now
    libterms = list()
    libterms.append(ConstantTerm())
    n = order  # max number of "blocks" to include
    k = len(observables)
    partitions = partition(n, k + 3)  # k observables + rho + 2 derivative dimensions
    # not a valid term if no observables or max exceeded
    for part in partitions:
        if part[k] > 0 and sum(part[:k]) <= max_observables and part[k] <= max_rho:  # popped a rho, did not exceed max observables
            # nt, nx = part[-2:]
            # obs_orders = part[:-2]
            # for tensor in raw_library_tensors(observables, obs_orders, nt, nx):
            # print("\n\n\n")
            # print("Partition:", part)
            for tensor in raw_library_tensors(observables, list(part)):
                if tensor.complexity <= order:  # this may not be true since we set complexity of rho[1]>1
                    # print("Tensor", tensor)
                    # print("List of labels", list_labels(tensor))
                    for label in list_labels(tensor):
                        # print("Label", label)
                        index_list = labels_to_index_list(label, len(tensor.obs_list))
                        # print("Index list", index_list)
                        for lt in get_library_terms(tensor, index_list):
                            # print("LT", lt)
                            # note: not sure where to put this check
                            canon = lt.canonicalize()
                            if lt.is_canonical:
                                # print("is canonical")
                                libterms.append(lt)
    return libterms


def get_valid_reorderings(observables, obs_index_list):
    if len(obs_index_list) == 0:  # don't think this actually happens, but just in case
        yield []
        return
    if len(obs_index_list[0]) == 0:
        for reorder in get_valid_reorderings(observables[1:], obs_index_list[1:]):
            yield [[]] + reorder
            return
    unique_perms = []
    for perm in permutations(obs_index_list[0]):
        if perm not in unique_perms:
            unique_perms.append(perm)
            if observables[0].cgp.is_index_canon(perm):
                for reorder in get_valid_reorderings(observables[1:], obs_index_list[1:]):
                    yield [list(perm)] + reorder


def get_library_terms(tensor, index_list):
    # distribute indexes in CGP according to all permutations that are canonical (with only those indices)
    der_index_list = index_list[0::2]
    obs_index_list = index_list[1::2]
    for perm_list in get_valid_reorderings(tensor.obs_list, obs_index_list):
        # print("perm_list:", perm_list)
        # noinspection PyTypeChecker
        yield LibraryTerm(tensor, index_list=flatten(zip(der_index_list, perm_list)))


class Equation(object):  # can represent equation (expression = 0) OR expression
    def __init__(self, term_list, coeffs):  # terms are LibraryTerms, coeffs are real numbers
        content = zip(term_list, coeffs)
        sorted_content = sorted(content, key=lambda x: x[0])
        # note that sorting guarantees canonicalization in equation term order
        self.term_list = [e[0] for e in sorted_content]
        self.coeffs = [e[1] for e in sorted_content]
        self.rank = term_list[0].rank
        self.complexity = sum([term.complexity for term in term_list])  # another choice is simply the number of terms

    def __add__(self, other):
        if isinstance(other, Equation):
            return Equation(self.term_list + other.term_list, self.coeffs + other.coeffs)
        else:
            raise TypeError(f"Second argument {other}) is not an equation.")

    def __rmul__(self, other):
        if isinstance(other, LibraryTerm):
            return Equation([(other * term).canonicalize() for term in self.term_list], self.coeffs)
        else:  # multiplication by number
            return Equation(self.term_list, [other * c for c in self.coeffs])

    def __mul__(self, other):
        return self.__rmul__(other)

    def __repr__(self):
        repstr = [str(coeff) + ' * ' + str(term) + ' + ' for term, coeff in zip(self.term_list, self.coeffs)]
        return reduce(add, repstr)[:-3]

    def __str__(self):
        return self.__repr__() + " = 0"

    def __eq__(self, other):
        return self.term_list == other.term_list and self.coeffs == other.coeffs

    def dt(self):
        components = [coeff * term.dt() for term, coeff in zip(self.term_list, self.coeffs)
                      if not isinstance(term, ConstantTerm)]
        if not components:
            return None
        return reduce(add, components).canonicalize()

    def dx(self):
        components = [coeff * term.dx() for term, coeff in zip(self.term_list, self.coeffs)
                      if not isinstance(term, ConstantTerm)]
        if not components:
            return None
        return reduce(add, components).canonicalize()

    def canonicalize(self):
        if len(self.term_list) == 0:
            return self
        term_list = []
        coeffs = []
        i = 0
        while i < len(self.term_list):
            reps = 0
            prev = self.term_list[i]
            while i < len(self.term_list) and prev == self.term_list[i]:
                reps += self.coeffs[i]
                i += 1
            term_list.append(prev)
            coeffs.append(reps)
        return Equation(term_list, coeffs)

    def eliminate_complex_term(self, return_normalization=False):
        if len(self.term_list) == 1:
            return self.term_list[0], None
        lhs = max(self.term_list, key=lambda t: t.complexity)
        lhs_ind = self.term_list.index(lhs)
        new_term_list = self.term_list[:lhs_ind] + self.term_list[lhs_ind + 1:]
        new_coeffs = self.coeffs[:lhs_ind] + self.coeffs[lhs_ind + 1:]
        new_coeffs = [-c / self.coeffs[lhs_ind] for c in new_coeffs]
        rhs = Equation(new_term_list, new_coeffs)
        if return_normalization:
            return lhs, rhs, self.coeffs[lhs_ind]
        return lhs, rhs

    def to_term(self):
        if len(self.term_list) != 1:
            raise ValueError("Equation contains more than one distinct term")
        else:
            return self.term_list[0]


class TermSum(Equation):
    def __init__(self, term_list):  # terms are LibraryTerms, coeffs are real numbers
        self.term_list = sorted(term_list)
        self.coeffs = [1] * len(term_list)
        self.rank = term_list[0].rank

    def __str__(self):
        repstr = [str(term) + ' + ' for term in self.term_list]
        return reduce(add, repstr)[:-3]

    def __add__(self, other):
        if isinstance(other, TermSum):
            return TermSum(self.term_list + other.term_list)
        elif isinstance(other, Equation):
            return Equation(self.term_list + other.term_list, self.coeffs + other.coeffs)
        else:
            raise TypeError(f"Second argument {other}) is not an equation.")
