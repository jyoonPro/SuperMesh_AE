/******************************************************************************
This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
*******************************************************************************/

#include <cassert>
#include <tacos/topology/kite_medium.h>
#include <iostream>
#include <vector>
#include <sstream>
#include <string>

using namespace tacos;

KiteMedium::KiteMedium(const int width,
                       const int height,
                       const Latency latency,
                       const Bandwidth bandwidth) noexcept
                       : width(width),
                         height(height) {
    assert(width > 0);
    assert(height > 0);
    assert(latency >= 0);
    assert(bandwidth > 0);

    // compute NPUs count
    int nodes = width * height;
    setNpusCount(width * height);

    connect(0, 1, latency, bandwidth, false);
    connect(0, 4, latency, bandwidth, false);
    connect(0, 2, latency, bandwidth, false);
    connect(0, 8, latency, bandwidth, false);

    connect(1, 0, latency, bandwidth, false);
    connect(1, 3, latency, bandwidth, false);
    connect(1, 9, latency, bandwidth, false);
    connect(1, 6, latency, bandwidth, false);

    connect(2, 0, latency, bandwidth, false);
    connect(2, 3, latency, bandwidth, false);
    connect(2, 5, latency, bandwidth, false);
    connect(2, 10, latency, bandwidth, false);

    connect(3, 2, latency, bandwidth, false);
    connect(3, 1, latency, bandwidth, false);
    connect(3, 7, latency, bandwidth, false);
    connect(3, 11, latency, bandwidth, false);

    connect(4, 0, latency, bandwidth, false);
    connect(4, 5, latency, bandwidth, false);
    connect(4, 6, latency, bandwidth, false);
    connect(4, 12, latency, bandwidth, false);

    connect(5, 4, latency, bandwidth, false);
    connect(5, 13, latency, bandwidth, false);
    connect(5, 2, latency, bandwidth, false);
    connect(5, 7, latency, bandwidth, false);

    connect(6, 1, latency, bandwidth, false);
    connect(6, 4, latency, bandwidth, false);
    connect(6, 7, latency, bandwidth, false);
    connect(6, 14, latency, bandwidth, false);

    connect(7, 3, latency, bandwidth, false);
    connect(7, 5, latency, bandwidth, false);
    connect(7, 6, latency, bandwidth, false);
    connect(7, 15, latency, bandwidth, false);

    connect(8, 0, latency, bandwidth, false);
    connect(8, 9, latency, bandwidth, false);
    connect(8, 12, latency, bandwidth, false);
    connect(8, 10, latency, bandwidth, false);

    connect(9, 1, latency, bandwidth, false);
    connect(9, 11, latency, bandwidth, false);
    connect(9, 8, latency, bandwidth, false);
    connect(9, 14, latency, bandwidth, false);

    connect(10, 2, latency, bandwidth, false);
    connect(10, 8, latency, bandwidth, false);
    connect(10, 13, latency, bandwidth, false);
    connect(10, 11, latency, bandwidth, false);

    connect(11, 3, latency, bandwidth, false);
    connect(11, 9, latency, bandwidth, false);
    connect(11, 10, latency, bandwidth, false);
    connect(11, 15, latency, bandwidth, false);

    connect(12, 4, latency, bandwidth, false);
    connect(12, 14, latency, bandwidth, false);
    connect(12, 8, latency, bandwidth, false);
    connect(12, 13, latency, bandwidth, false);

    connect(13, 5, latency, bandwidth, false);
    connect(13, 15, latency, bandwidth, false);
    connect(13, 12, latency, bandwidth, false);
    connect(13, 10, latency, bandwidth, false);

    connect(14, 9, latency, bandwidth, false);
    connect(14, 6, latency, bandwidth, false);
    connect(14, 12, latency, bandwidth, false);
    connect(14, 15, latency, bandwidth, false);

    connect(15, 11, latency, bandwidth, false);
    connect(15, 7, latency, bandwidth, false);
    connect(15, 14, latency, bandwidth, false);
    connect(15, 13, latency, bandwidth, false);

    for (auto h = 0; h < height; h++){
        for (auto w = 0; w < width - 1; w++){
            const auto src = (h * width) + w;
            const auto dest = src + 1;
            std::cout << getLatency(src, dest) << " ";
        }
        std::cout << std::endl;
    }
}
