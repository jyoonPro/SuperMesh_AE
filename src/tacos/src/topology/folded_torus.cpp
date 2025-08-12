/******************************************************************************
This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
*******************************************************************************/

#include <cassert>
#include <tacos/topology/folded_torus.h>
#include <iostream>
#include <vector>
#include <sstream>
#include <string>

using namespace tacos;

std::vector<int> getFirstDimensionNodes(int node, int nodes_in_first_dim) {
    int row_index = node / nodes_in_first_dim;
    int row_start_index = row_index * nodes_in_first_dim;
    std::vector<int> node_list;

    for (int i = 0; i < nodes_in_first_dim; ++i) {
        node_list.push_back(row_start_index + i);
    }

    return node_list;
}

std::vector<int> getSecondDimensionNodes(int node, int nodes_in_first_dim, int nodes_in_second_dim) {
    int col_index = node % nodes_in_first_dim;
    std::vector<int> node_list;
    for (int i = 0; i < nodes_in_second_dim; ++i) {
        node_list.push_back(nodes_in_first_dim * i + col_index);
    }
    return node_list;
}

FoldedTorus::FoldedTorus(const int width,
                         const int height,
                         const Latency latency_high,
                         const Bandwidth bandwidth_high,
                         const Latency latency_low,
                         const Bandwidth bandwidth_low) noexcept
                         : width(width),
                           height(height) {
    assert(width > 0);
    assert(height > 0);
    assert(latency_high >= 0);
    assert(bandwidth_high > 0);
    assert(latency_low >= 0);
    assert(bandwidth_low > 0);
    // Here low means lower length link and high means higher length links

    // compute NPUs count
    int nodes = width * height;
    setNpusCount(width * height);

    for (int node = 0; node < nodes; node++) {
        for (int dim = 0; dim < 2; ++dim) {
            std::vector<int> dimension_nodes;
            if (dim == 0) {
                dimension_nodes = getFirstDimensionNodes(node, width);
            } else if (dim == 1) {
                dimension_nodes = getSecondDimensionNodes(node, width, height);
            }

            auto it = std::find(dimension_nodes.begin(), dimension_nodes.end(), node);
            int node_index = std::distance(dimension_nodes.begin(), it);

            if (node_index == 0) {
                connect(node, dimension_nodes[2], latency_high, bandwidth_high, false);
                connect(node, dimension_nodes[1], latency_low, bandwidth_low, false);
            } else if (node_index == 1) {
                connect(node, dimension_nodes[3], latency_high, bandwidth_high, false);
                connect(node, dimension_nodes[0], latency_low, bandwidth_low, false);
            } else if (node_index == dimension_nodes.size() - 2) {
                connect(node, dimension_nodes[node_index + 1], latency_low, bandwidth_low, false);
                connect(node, dimension_nodes[node_index - 2], latency_high, bandwidth_high, false);
            } else if (node_index == dimension_nodes.size() - 1) {
                connect(node, dimension_nodes[node_index - 1], latency_low, bandwidth_low, false);
                connect(node, dimension_nodes[node_index - 2], latency_high, bandwidth_high, false);
            } else {
                connect(node, dimension_nodes[node_index + 2], latency_high, bandwidth_high, false);
                connect(node, dimension_nodes[node_index - 2], latency_high, bandwidth_high, false);
            }
        }
    }

    for (auto h = 0; h < height; h++){
        for (auto w = 0; w < width - 1; w++){
            const auto src = (h * width) + w;
            const auto dest = src + 1;
            std::cout << getLatency(src, dest) << " ";
        }
        std::cout << std::endl;
    }
}
